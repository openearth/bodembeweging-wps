import configparser


def pgconfig(fn, section="postgres"):
    config = configparser.ConfigParser()
    config.read(fn)
    secrets = {key: value for (key, value) in config.items(section)}
    return secrets

#if __name__ == "__main__":
#    print pgconfig("dbconf.ini")
