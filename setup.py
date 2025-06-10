from fmtr.tools import Setup

setup = Setup(
    dependencies=dict(
        install=['fmtr.tools[version,logging,dns,http,patterns,sets,yaml]'],
    ),
    description='Home lab DNS server'
)
