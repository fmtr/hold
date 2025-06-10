def main():
    from fmtr.tools import debug
    debug.trace()
    from fmtr.dns.settings import Settings
    settings = Settings()
    settings.server.start()


if __name__ == '__main__':
    main()
