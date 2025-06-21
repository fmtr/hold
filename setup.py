from fmtr.tools import Setup

setup = Setup(
    dependencies=dict(
        install=['fmtr.tools[version.dev,logging,dns,http,patterns,sets,yaml,debug,caching,api]==1.3.21'],
    ),
    description='Homelab AdBlocking DNS Server'
)
