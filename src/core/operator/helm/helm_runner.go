// Package helm runs helm subprocesses to install/upgrade/uninstall helm charts.
// It runs each chart's helm operations run sequentially.
// It schedules the subprocesses to bound total memory usage.
package helm

import (
	"bytes"
	"context"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"syscall"
	"time"

	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"

	core "k8s.io/api/core/v1"
)

// RunnerOptions are parameters passed to Start.
type RunnerOptions struct {
	// Maximum memory used for all helm subprocess together at any given time.
	MaxMemoryBytes int

	// Maximum memory used for a single helm operation (subprocess).
	MaxMemoryBytesPerOp int

	// Maximum memory used for a helm operation keyed by chart to set different
	// limits for different charts if desired. If a charts is not found in this
	// map the limit used will be the default MaxMemoryBytesPerOp.
	MaxMemoryBytesPerOpByChart map[string]int

	// Maximum allowed time to run a helm repo update.
	RepoUpdateTimeout time.Duration

	// Maximum allowed time to run a helm install or upgrade.
	InstallTimeout time.Duration

	// Maximum allowed time to run a helm uninstall.
	UninstallTimeout time.Duration
}

// A Chart value identifies a helm chart from this package's point of view.
// Install/Uninstall operations on the same Chart are serialized, they will
// never run concurrent with each other. They are allowed to run concurrent
// with the operations on other Charts.
type Chart struct {
	Namespace string // The namespace to install to.
	Name      string // The name of the chart, including the repo name.
	Release   string // The name of the release to install it as.
}

// An InstallArgs value specifies the parameters to install a chart.
type InstallArgs struct {
	RepoURL    string
	RepoName   string
	Version    string
	ValuesName string
}

// globals
var (
	// Runner options / parameters.
	opts RunnerOptions

	// Install/uninstall operations channel.
	opChan chan operation

	// Feedback channel for spawned operation goroutines to communicate to the
	// run loop that they have finished.
	doneChan chan Chart

	// Kubernetes client.
	kc client.Client

	// Logger.
	log = ctrl.Log.WithName("helm")
)

// Start starts the runner, the goroutine that coordinates helm operations. Call
// it once at most. Cancelling the context signals starting to shut down. No
// more helm operations are spawned, and the runner waits for running ones. Once
// there are no more running operations it signals completion by closing the
// returned channel.
func Start(ctx context.Context, options RunnerOptions, client client.Client) chan struct{} {
	if opChan != nil {
		panic("Start called more than once")
	}
	opts = options
	opChan = make(chan operation)
	doneChan = make(chan Chart)
	kc = client
	allDoneChan := make(chan struct{})
	go run(ctx, allDoneChan)
	return allDoneChan
}

// Request that a helm chart be installed.
func Install(chart Chart, args InstallArgs) {
	opChan <- operation{opInstall, chart, &args}
}

// Request that a helm chart be uninstalled.
func Uninstall(chart Chart) {
	opChan <- operation{opUninstall, chart, nil}
}

type opKind byte

const (
	opInstall   opKind = 'i'
	opUninstall opKind = 'u'
)

type operation struct {
	kind  opKind
	chart Chart
	args  *InstallArgs
}

func (op *operation) summary() string {
	return fmt.Sprintf("%c %s", op.kind, op.chart.Release)
}

// This state must only accessed by the run loop goroutine.
type state struct {
	// One pending operation per chart. If further operations are requested for a
	// chart while there is one running the last request overwrites previous ones.
	pending map[Chart]*operation

	// Running operations. A single operation is allowed to run at once per chart.
	// The value is the memory allocated for use by the operation, in bytes.
	running map[Chart]int
}

func (s *state) memoryInUse() int {
	inUseMem := 0
	for _, mem := range s.running {
		inUseMem += mem
	}
	return inUseMem
}

func (s *state) memoryForOperation(op *operation) int {
	if mem, found := opts.MaxMemoryBytesPerOpByChart[op.chart.Name]; found {
		return mem
	}
	return opts.MaxMemoryBytesPerOp
}

func (s *state) enoughMemoryForOperation(op *operation) bool {
	return s.memoryForOperation(op) <= opts.MaxMemoryBytes-s.memoryInUse()
}

func run(ctx context.Context, allDoneChan chan struct{}) {
	s := &state{
		pending: map[Chart]*operation{},
		running: map[Chart]int{},
	}

	for {
		select {
		// Context cancelled.
		case <-ctx.Done():
			log.Info("context cancelled")
			// Wait for all spawned goroutines to finish.
			for len(s.running) > 0 {
				delete(s.running, <-doneChan)
			}
			close(allDoneChan) // Signal that we are done.
			return

		// Operation received.
		case op := <-opChan:
			log.Info("operation received")
			s.pending[op.chart] = &op

		// Operation done.
		case chart := <-doneChan:
			log.Info("operation done")
			delete(s.running, chart)
		}

		log.Info("status", "pending", len(s.pending), "running", len(s.running))

		// Spawn pending operations if possible.
		// NOTE: From the go spec "The iteration order over maps is not specified
		// and is not guaranteed to be the same from one iteration to the next."
		// The fairness of the scheduling we do here will be determined by go's
		// map iteration algorithm. This could be a problem.
		// See: https://dev.to/wallyqs/gos-map-iteration-order-is-not-that-random-mag
		for chart, op := range s.pending {
			if _, opRunning := s.running[chart]; opRunning {
				log.Info("skiping pending op (already running)", "chart", op.chart)
				continue
			}
			if !s.enoughMemoryForOperation(op) {
				log.Info("skiping pending op (not enough memory)", "chart", op.chart)
				continue
			}

			log.Info("spawn operation", "op", op.summary(), "chart", op.chart)
			delete(s.pending, chart)
			s.running[chart] = s.memoryForOperation(op)
			go runOperation(ctx, op)
		}
	}
}

func runOperation(ctx context.Context, op *operation) {
	defer func() { doneChan <- op.chart }()
	var err error
	switch op.kind {
	case opInstall:
		err = runInstall(ctx, op)
		if err != nil {
			// NOTE: Once this is logged, the operation has been processed. It won't
			// be retried. A programmer needs to look at this error and fix it. If
			// it can be fixed by retrying something, do the retries within the
			// operation, and don't surface the error to here.
			log.Error(err, "helm error", "op", op.summary(), "chart", op.chart)
		}
	case opUninstall:
		// NOTE: We're not interested on raising uninstall errors since it's most
		// likely that the release was already uninstalled on a previous reconcile
		runUninstall(ctx, op)
	}
}

func runInstall(ctx context.Context, op *operation) error {
	// TODO: Don't run helm update on every install, it takes significant time
	// and is not needed most times. Only run it if it hasn't run for a while.
	if err := runRepoUpdate(ctx, op); err != nil {
		return err
	}
	valuesFile, err := downloadValues(ctx, op)
	if err != nil {
		return err
	}
	defer os.Remove(valuesFile)
	return runCommand(ctx, opts.InstallTimeout,
		"helm", "-n", op.chart.Namespace, "upgrade", "-i",
		op.chart.Release, op.chart.Name,
		"--version", op.args.Version,
		"-f", valuesFile,
	)
}

func runUninstall(ctx context.Context, op *operation) error {
	return runCommand(ctx, opts.UninstallTimeout,
		"helm", "-n", op.chart.Namespace, "uninstall",
		op.chart.Release,
	)
}

func runRepoUpdate(ctx context.Context, op *operation) error {
	if err := runCommand(ctx, opts.RepoUpdateTimeout,
		"helm", "-n", op.chart.Namespace, "repo", "add",
		op.args.RepoName, op.args.RepoURL,
	); err != nil {
		return err
	}
	return runCommand(ctx, opts.RepoUpdateTimeout,
		"helm", "-n", op.chart.Namespace, "repo", "update",
		op.args.RepoName,
	)
}

// NOTE: We need to depend on a kubernetes client to fetch the values. Having
// the full helm values as InstallArgs is not desirable, the request would have
// to be done to early, and those values would have to live in memory for longer
// than they have to. If we really wanted to cut the dependency on the client
// we could take a getValues closure in InstallArgs that makes the request to
// fetch the values when called.
func downloadValues(ctx context.Context, op *operation) (string, error) {
	ns := op.chart.Namespace
	name := op.args.ValuesName

	valuesFile := os.TempDir() + "/" + name + "-values.yaml"

	valuesObj := core.ConfigMap{}
	err := kc.Get(ctx, client.ObjectKey{Namespace: ns, Name: name}, &valuesObj)
	if err != nil {
		return "", err
	}
	values, ok := valuesObj.Data["values.yaml"]
	if !ok {
		return "", fmt.Errorf("values configmap data must have values.yaml: %s", name)
	}

	if err := os.WriteFile(valuesFile, []byte(values), 0644); err != nil {
		return "", err
	}

	return valuesFile, nil
}

func runCommand(ctx context.Context, timeout time.Duration, name string, arg ...string) error {
	log.Info("running command", "command", cmdline(name, arg))
	// cmdCtx is not a child of ctx because if it was the subprocess would be
	// KILLed right away when cancelled and if this happens we cannot try to
	// TERMinate it first.
	cmdCtx, cmdCancel := context.WithCancel(context.Background())
	cmd := exec.CommandContext(cmdCtx, name, arg...)
	defer cmdCancel()
	// NOTE: bytes.Buffer will grow as needed to fit helm's stderr. We can tail
	// the output to a circular buffer instead if we want to cap memory usage.
	var stderr bytes.Buffer
	cmd.Stderr = &stderr
	// NOTE: If we also want stdout we can add: `cmd.Stdout = &stderr`.
	if err := cmd.Start(); err != nil {
		return err
	}
	go func() {
		// Wait until the command finishes or ctx is cancelled.
		select {
		// The operation's context has been cancelled. Terminate the subprocess.
		case <-ctx.Done():
			// We first try sending SIGTERM, to give helm a chance to clean up.
			// Hopefully this way we avoid helm release secret corruption.
			// see: https://github.com/helm/helm/pull/9180
			cmd.Process.Signal(syscall.SIGTERM)
			time.Sleep(time.Second)
			// Cancel cmdCtx to ensure the process exits. If still alive it will
			// be sent SIGKILL.
			cmdCancel()
		case <-cmdCtx.Done():
		}
	}()
	if err := cmd.Wait(); err != nil {
		return fmt.Errorf("runCommand(%s): %w: %s", cmdline(name, arg), err, stderr.String())
	}
	return nil
}

func cmdline(name string, arg []string) string {
	return name + " " + strings.Join(arg, " ")
}
