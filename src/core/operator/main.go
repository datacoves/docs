package main

import (
	"flag"
	"os"
	"time"

	// Import all Kubernetes client auth plugins (e.g. Azure, GCP, OIDC, etc.)
	// to ensure that exec-entrypoint and run can make use of them.
	_ "k8s.io/client-go/plugin/pkg/client/auth"

	"github.com/TheZeroSlave/zapsentry"
	"github.com/getsentry/sentry-go"
	"github.com/go-logr/zapr"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
	"k8s.io/apimachinery/pkg/runtime"
	utilruntime "k8s.io/apimachinery/pkg/util/runtime"
	clientgoscheme "k8s.io/client-go/kubernetes/scheme"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/healthz"
	ctrlzap "sigs.k8s.io/controller-runtime/pkg/log/zap"

	datacovescomv1 "datacoves.com/operator/api/v1"
	"datacoves.com/operator/controllers"
	"datacoves.com/operator/helm"
	//+kubebuilder:scaffold:imports
)

var (
	scheme   = runtime.NewScheme()
	setupLog = ctrl.Log.WithName("setup")
)

func init() {
	utilruntime.Must(clientgoscheme.AddToScheme(scheme))

	utilruntime.Must(datacovescomv1.AddToScheme(scheme))
	//+kubebuilder:scaffold:scheme
}

func main() {
	var metricsAddr string
	var enableLeaderElection bool
	var probeAddr string
	flag.StringVar(&metricsAddr, "metrics-bind-address", ":8080", "The address the metric endpoint binds to.")
	flag.StringVar(&probeAddr, "health-probe-bind-address", ":8081", "The address the probe endpoint binds to.")
	flag.BoolVar(&enableLeaderElection, "leader-elect", false,
		"Enable leader election for controller manager. "+
			"Enabling this will ensure there is only one active controller manager.")
	opts := ctrlzap.Options{
		Development: true,
		TimeEncoder: zapcore.ISO8601TimeEncoder,
	}
	opts.BindFlags(flag.CommandLine)
	flag.Parse()

	// Logging setup. A bit of a mess. The operator uses logr.Logger, which is
	// what kubebuilder and controller-runtime come with. Logr is an interface
	// package. The backend used is zap, through the zapr package. The package
	// controller-runtime/pkg/log/zap wraps zapr to set some default options and
	// provides utilities to configure the zap logger from command line flags.
	// To integrate sentry with the zap/logr loggers we use the zapsentry package.
	// It takes a *zap.Logger to attach to, which we get from ctrlzap.NewRaw.
	sentryDsn, ok := os.LookupEnv("SENTRY_DSN")
	var sentryClient *sentry.Client
	var err error
	if ok {
		// TODO: Sentry defaults to HTTP. Use HTTPS.
		sentryClient, err = sentry.NewClient(sentry.ClientOptions{
			Dsn:              sentryDsn,
			Release:          os.Getenv("SENTRY_RELEASE"),
			Environment:      os.Getenv("SENTRY_ENVIRONMENT"),
			AttachStacktrace: true,
		})
		// NOTE: This waits for a second before exiting for sentry to flush.
		// Are there any unintended consequences from doing this?
		defer sentryClient.Flush(time.Second)
	}
	if ok && err == nil {
		zapLogger := ctrlzap.NewRaw(ctrlzap.UseFlagOptions(&opts))
		zapLogger = modifyToSentryLogger(zapLogger, sentryClient)
		ctrl.SetLogger(zapr.NewLogger(zapLogger))
		setupLog.Info("sentry configured")
	} else {
		ctrl.SetLogger(ctrlzap.New(ctrlzap.UseFlagOptions(&opts)))
		if !ok {
			setupLog.Info("SENTRY_DSN not set")
		} else {
			setupLog.Error(err, "unable to create sentry client")
		}
	}

	leaseDuration := 30 * time.Second // Default is 15 seconds.
	renewDeadline := 20 * time.Second // Default is 10 seconds.
	mgr, err := ctrl.NewManager(ctrl.GetConfigOrDie(), ctrl.Options{
		Scheme:                 scheme,
		MetricsBindAddress:     metricsAddr,
		Port:                   9443,
		HealthProbeBindAddress: probeAddr,
		LeaderElection:         enableLeaderElection,
		LeaderElectionID:       "5c393c71.datacoves.com",
		LeaseDuration:          &leaseDuration,
		RenewDeadline:          &renewDeadline,
	})
	if err != nil {
		setupLog.Error(err, "unable to start manager")
		os.Exit(1)
	}

	if err = (&controllers.WorkspaceReconciler{
		Client: mgr.GetClient(),
		Scheme: mgr.GetScheme(),
	}).SetupWithManager(mgr); err != nil {
		setupLog.Error(err, "unable to create controller", "controller", "Workspace")
		os.Exit(1)
	}
	if err = (&controllers.UserReconciler{
		Client: mgr.GetClient(),
		Scheme: mgr.GetScheme(),
	}).SetupWithManager(mgr); err != nil {
		setupLog.Error(err, "unable to create controller", "controller", "User")
		os.Exit(1)
	}
	if err = (&controllers.HelmReleaseReconciler{
		Client: mgr.GetClient(),
		Scheme: mgr.GetScheme(),
	}).SetupWithManager(mgr); err != nil {
		setupLog.Error(err, "unable to create controller", "controller", "HelmRelease")
		os.Exit(1)
	}
	// if err = (&controllers.AccountReconciler{
	// 	Client: mgr.GetClient(),
	// 	Scheme: mgr.GetScheme(),
	// }).SetupWithManager(mgr); err != nil {
	// 	setupLog.Error(err, "unable to create controller", "controller", "Account")
	// 	os.Exit(1)
	// }
	//+kubebuilder:scaffold:builder

	if err := mgr.AddHealthzCheck("healthz", healthz.Ping); err != nil {
		setupLog.Error(err, "unable to set up health check")
		os.Exit(1)
	}
	if err := mgr.AddReadyzCheck("readyz", healthz.Ping); err != nil {
		setupLog.Error(err, "unable to set up ready check")
		os.Exit(1)
	}

	// NOTE: On helm subprocess termination:
	// - https://go.dev/ref/spec#Program_execution
	//   Go programs exit when the main goroutine exits. They don't wait for other
	//   running goroutines to finish. We need to do it.
	// - https://go.dev/blog/context
	// - https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination
	//	 Kubernetes sends TERM, waits for a gracePeriod (manager.yaml), then KILLs.
	//
	// When the operator gets TERM, the ctx below is cancelled. The helm package
	// stops taking install/uninstall request at this point, and starts waiting
	// for all subprocesses to finish. If they don't finish within the grace
	// period the operator will be KILLed. The subprocesses are most likely
	// orphaned and killed. Killing helm can leave it's release kubernetes
	// secret in a bad state (PendingUpgrade). Some things we can do:
	//
	// 1. Increase the grace period significantly to let subprocesses finish.
	//    Unlikely that we can/want to increase it enough to ensure any helm
	//    subprocess completes normally.
	// 2. Forward the TERM signal to the subprocesses. This probably lets helm
	//    shut down more gracefully (https://github.com/helm/helm/pull/9180).
	// 3. As a last resort, when helm was KILLed and the release is in a bad
	//    state, try to recover by deleting the release secret, a la nuke_helm_release.

	// This starts a goroutine that cancels ctx is on TERM, and os.Exits on receiving
	// a second termination signal.
	ctx := ctrl.SetupSignalHandler()

	// We use the mgr kubernetes client, which does caching, etc. This couples
	// the helm package and the manager. If this leads to problems or difficulty
	// in undertanding how things are working we may be better off by having the
	// helm package setup its own non-caching kubernetes client.
	setupLog.Info("starting helm")
	helmOptions := helm.RunnerOptions{
		MaxMemoryBytes:      1000 * 1024 * 1024,
		MaxMemoryBytesPerOp: 50 * 1024 * 1024,
		RepoUpdateTimeout:   2 * time.Minute,
		InstallTimeout:      20 * time.Minute,
		UninstallTimeout:    10 * time.Minute,
	}
	helmDone := helm.Start(ctx, helmOptions, mgr.GetClient())

	setupLog.Info("starting manager")
	err = mgr.Start(ctx)
	if err != nil {
		setupLog.Error(err, "problem running manager")
	}

	// The ctx has been cancelled. Wait for the helm runner goroutine to finish.
	<-helmDone

	if err != nil {
		os.Exit(1)
	}
}

func modifyToSentryLogger(log *zap.Logger, client *sentry.Client) *zap.Logger {
	cfg := zapsentry.Configuration{
		Level:             zapcore.ErrorLevel,
		EnableBreadcrumbs: false, // TODO: Enable if we use them.
	}
	core, err := zapsentry.NewCore(cfg, zapsentry.NewSentryClientFromClient(client))

	// In case of err it will return noop core. So, we can safely attach it.
	if err != nil {
		log.Warn("failed to init zap", zap.Error(err))
	}

	log = zapsentry.AttachCoreToLogger(core, log)

	// To use breadcrumbs feature - create new scope explicitly
	// and attach after attaching the core.
	return log.With(zapsentry.NewScope())
}
