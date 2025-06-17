# Choosing an ec2 instance type and estimating pods per node

[AWS docs.][choosing]

## Pod limit from network constraints

Every pod must have an IP. EC2 instances have a maximum number of IPs, which
limits the number of pods per node. [source][eni-max-pods]

With CNI version 1.9 or higher and nitro instances, [the pod limit can be increased][eni-max-pods-update].
For example:

```
 $ ./max-pods-calculator.sh --instance-type m5.large --cni-version 1.9.0
29

 $ ./max-pods-calculator.sh --instance-type m5.large --cni-version 1.9.0 --cni-prefix-delegation-enabled
110

# For ensembledev.apps.jnj.com:
$ ./max-pods-calculator.sh --instance-type m5.4xlarge --cni-version 1.7.1
110
```

[List of ENI and IP limits per instance type][instance-max-eni].


## Pod limit from volume attachment limits

Currently some of our pods (code-server) require ELB volumes. EC2 instances have
a maximum number of volumes that can be attached. For "most" nitro instances, the
sum of ENIs, volume attachments and instance store volumes must be less than 28.
[source][vol-max-pods]. Volume attachments seem capped by 26 because the mount
points use the a letter of the alphabet each.



[choosing]: https://docs.aws.amazon.com/eks/latest/userguide/choosing-instance-type.html
[eni-max-pods]: https://raw.githubusercontent.com/awslabs/amazon-eks-ami/master/files/eni-max-pods.txt
[eni-max-pods-update]: https://aws.amazon.com/blogs/containers/amazon-vpc-cni-increases-pods-per-node-limits/
[instance-max-eni]: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html#AvailableIpPerENI
[vol-max-pods]: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/volume_limits.html
