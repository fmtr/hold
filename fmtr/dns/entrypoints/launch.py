def main():
    from fmtr.tools import debug
    debug.trace()
    from fmtr.dns.obs import logger
    from fmtr.dns.paths import paths
    from fmtr.dns.version import __version__
    logger.info(f'Launching {paths.name_ns} {__version__=} from entrypoint.')

    logger.debug(f'{paths.settings.exists()=} {str(paths.settings)=}')
    with logger.span(f'Reading settings...'):
        from fmtr.dns.settings import Settings
        settings = Settings()

    logger.info(f'Launching server...')
    settings.server.start()


if __name__ == '__main__':
    main()
