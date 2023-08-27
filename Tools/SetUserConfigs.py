import os
import json
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

    # param "models" consist of the name of the model as key and is version as value
    if args.key == "models":
        # Convert models dict in cmd request to dict
        _new_models = json.loads(args.value)
        # Get allready installed models
        _old_models = user_config["models"]
        if not _old_models:
            _old_models = {}
        # Instatiate result models
        _res_models = dict(_old_models)
        for _model, _version in _new_models.items():
            if _model in _res_models:
                if _res_models[_model] == _version:
                    continue
                _res_models[_model] = _version
                continue
            _res_models.update({_model:_version})
        # Update user_config `models`
        user_config[args.key] = _res_models
    else:
        user_config[args.key] = args.value

    with open(os.path.join(config_folder, "user.config.yaml"), 'w',) as fw:
        yaml.dump(user_config,fw,sort_keys=False)



if __name__ == "__main__":
    args = parser.parse_args()
    main(args)