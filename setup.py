from fmtr.tools import Setup, Tools

setup = Setup(
    dependencies=dict(
        install=['numpy', 'pandas', Tools('version', 'logging')],
    ),
    description='{description}'
)
