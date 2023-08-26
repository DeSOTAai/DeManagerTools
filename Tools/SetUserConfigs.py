import os
import yaml
from yaml.loader import SafeLoader
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-k", "--key", 
                    type=str)
parser.add_argument("-v", "--value", 
                    type=str)

# Get User Configs
user_path=os.path.expanduser('~')
desota_root_path=os.path.join(user_path, "Desota")
config_folder=os.path.join(desota_root_path, "Configs")  # User | Services
with open(os.path.join(config_folder, "user.config.yaml")) as f:
    USER_CONF = yaml.load(f, Loader=SafeLoader)


# Set User Configs
def main(args):
    user_config = USER_CONF

    user_config[args.key] = args.value

    with open(os.path.join(config_folder, "user.config.yaml"), 'w',) as fw:
        yaml.dump(user_config,fw,sort_keys=False)



if __name__ == "__main__":
    args = parser.parse_args()
    main(args)