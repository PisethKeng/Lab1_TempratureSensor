def load_env(file=".env"):
    env = {}
    try:
        with open(file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, val = line.split("=", 1)
                        env[key.strip()] = val.strip()
    except Exception as e:
        print("env load error:", e)
    return env