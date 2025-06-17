# Install python requirements on bastion in JNJ

```
wget --no-check-certificate https://bootstrap.pypa.io/pip/3.6/get-pip.py && python3 get-pip.py --user
```

Then, cd into the datacoves_deployment cloned repo folder, and run:

```
pip install -r requirements.txt
```
