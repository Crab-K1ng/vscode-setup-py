import copy
import pprint
from setup_vscode import update_setting, uninstall_setting, print_header, print_end

# --------------------------
# Test data
# --------------------------

web_settings: dict = {
    "workbench.colorTheme": "Horizon",
    "files.autoSave": "afterDelay",
    "editor.formatOnSave": True,
    "terminal.integrated.defaultProfile.windows": "PowerShell",
    "[typescript]": {"editor.defaultFormatter": "esbenp.prettier-vscode"},
    "[html]": {
        "editor.defaultFormatter": "esbenp.prettier-vscode",
        "editor.suggest": {
            "insertMode": "replace",
            "otherSetting": True
        }
    },
    "[css]": {"editor.defaultFormatter": "esbenp.prettier-vscode"},
}

backup_settings = {
    "workbench.colorTheme": "Default",
    "files.autoSave": "off",
    "[typescript]": {"editor.defaultFormatter": "some.formatter"},
    "[html]": {
        "editor.defaultFormatter": "some.formatter",
        "editor.suggest": {"insertMode": "none"}
    }
}

current_settings = copy.deepcopy(backup_settings)

# --------------------------
# Helper functions
# --------------------------

def simulate_install():
    print_header("Installing settings")
    backup = copy.deepcopy(current_settings)
    update_setting(current_settings, web_settings)
    print_header("Settings AFTER Install")
    pprint.pprint(current_settings)
    print_end()
    return backup

def simulate_user_changes():
    print_header("User Changes AFTER Install")
    # Modify existing keys applied by script
    current_settings["workbench.colorTheme"] = "Solarized"
    current_settings["files.autoSave"] = "onFocusChange"
    # Add new keys not applied by script
    current_settings["editor.tabSize"] = 4
    # Deep nested user changes
    current_settings["[html]"]["editor.suggest"]["customUserSetting"] = 42
    current_settings["[html]"]["editor.formatOnSave"] = False

    current_settings["[test]"] = {}
    current_settings["[test]"]["test2"] = "test"

    pprint.pprint(current_settings)
    print_end()

def simulate_uninstall(backup):
    print_header("Uninstalling settings")
    uninstall_setting(current_settings, backup, web_settings)
    print_header("Settings AFTER Uninstall")
    pprint.pprint(current_settings)
    print_end()

# --------------------------
# Run simulations
# --------------------------

backup_settings_json = simulate_install()
simulate_user_changes()
simulate_uninstall(backup_settings_json)

# --------------------------
# Assertions to check behavior
# --------------------------

# Keys applied by web_settings should revert to backup
assert current_settings["workbench.colorTheme"] == "Default"
assert current_settings["files.autoSave"] == "off"
assert current_settings["[typescript]"]["editor.defaultFormatter"] == "some.formatter"
assert current_settings["[html]"]["editor.defaultFormatter"] == "some.formatter"
assert current_settings["[html]"]["editor.suggest"]["insertMode"] == "none"

# User-added keys should remain
assert current_settings["editor.tabSize"] == 4
assert current_settings["[html]"]["editor.suggest"]["customUserSetting"] == 42
assert current_settings["[html]"]["editor.formatOnSave"] is False

print("All deep nested tests passed!")
