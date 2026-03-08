from corio import Setup

setup = Setup(
    dependencies=dict(
        install=['corio[version.dev,logging,dns,http,patterns,sets,yaml,debug,caching,api]'],
    ),
)
