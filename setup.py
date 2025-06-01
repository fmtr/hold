from fmtr.tools import Setup, Tools

setup = Setup(
    dependencies=dict(
        install=[Tools('version', 'logging')],
    ),
    description='Home lab DNS server'
)
