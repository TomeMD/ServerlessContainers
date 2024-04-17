import numpy as np

from src.WattWizard.config.MyConfig import MyConfig
from src.WattWizard.model.ModelHandler import ModelHandler

my_config = MyConfig.get_instance()
model_handler = ModelHandler.get_instance()


def get_desired_power(req):
    value = req.args.get("desired_power", type=float)
    if value is None:
        raise TypeError(f"Missing desired power value in request. You must include it as follows"
                        f" <url>:<port>/predict?desired_power=<value>")
    return value


def time_series_to_train_data(model_instance, time_series):
    x_values = []
    for var in model_instance.get_model_vars():
        if var in time_series:
            x_values.append(time_series[var].values.reshape(-1, 1))
        else:
            raise TypeError(f"Missing variable {var} in train time series")
    x_stack = np.hstack(x_values)
    y = time_series["power"].values
    return x_stack, y


def json_to_train_data(model_instance, json_data):
    if "power" in json_data:
        y = np.array(json_data["power"])
    else:
        raise TypeError("Missing power data in JSON")
    x_values = []
    for var in model_instance.get_model_vars():
        if var not in json_data:
            raise TypeError(f"Missing {var} data in JSON")
        x_values.append(np.array(json_data[var]).reshape(-1, 1))
    x_stack = np.hstack(x_values)
    return x_stack, y


def request_to_dict(model_instance, request):
    x_values = {}
    for var in model_instance.get_model_vars():
        value = request.args.get(var, type=float)
        if value is not None:
            x_values[var] = value
        else:
            raise TypeError(f"Missing {var} value in request. You must include it as follows"
                            f" <url>:<port>/predict?{var}=<value>")
    return x_values