# -*- coding: utf-8 -*-

# Python modules imports
import argparse
import json
import os
from xml.etree import ElementTree as ET
import polib

CWD_PATH = os.path.dirname(os.path.abspath(__file__))


class ConfigMC(type):

    def __str__(cls):
        s = '* Configuration:'
        for k, v in cls._config.items():
            s += '\n\t- {}: {}'.format(k, str(v))
        return s


class Config(metaclass=ConfigMC):
    """Singleton class to define user configuration"""


    _config = {}

    @classmethod
    def get(cls, item):
        return cls._config[item]



    @classmethod
    def init_config(cls):

        parser = argparse.ArgumentParser(description='Catch-up TV & More simulator')

        parser.add_argument('-a', '--addon-path', default='', help='Path of plugin.video.catchuptvandmore')
        parser.add_argument('-c', '--config-file', default='', help='Optional JSON config file (if given, CLI args are not taken !!)')
        parser.add_argument('-s', '--console-size', type=int, default=160, help='Your console size in order to compute the width of the fake Kodi menu [160]')
        parser.add_argument('--entry-point', default='1', help='Entry point of the simulation (separate items with dashes (e.g. \'1-2-1-13\')) [1]')
        parser.add_argument('--exit-after-x-errors', type=int, default=-1, help='Exit simulator after N errors encountered [-1]')
        parser.add_argument('--disable-video-player', action='store_true', help='Do not open mpv on video selection')
        parser.add_argument('--kodi-version', default='LEIA', choices=['LEIA', 'KRYPTON', 'JARVIS'], help='Kodi version to simulate [LEIA]')
        parser.add_argument('--print-all-explored-items', action='store_true', help='Print all explored items when exit the simulator')
        parser.add_argument('--disable-image-check', action='store_true', help='Do not check image URL')
        parser.add_argument('--autoreload-addon', action='store_true', help='Auto reload addon source files (usefull during dev)')


        log_group = parser.add_argument_group('Logging')
        log_group.add_argument('--disable-kodi-log', action='store_true', help='Disable stdout Kodi logging')
        log_group.add_argument('--kodi-log-level', type=int, default=0, help='Minimum Kodi log level to be logging')
        log_group.add_argument('--disable-xbmcaddon-mock-log', action='store_true', help='Disable log messages of xbmcaddon module functions calls')
        log_group.add_argument('--disable-xbmc-mock-log', action='store_true', help='Disable log messages of xbmc module functions calls')


        auto_exploration_group = parser.add_argument_group('Auto exploration mode')
        auto_exploration_group.add_argument('--auto-exploration', action='store_true', help='Enable auto exploration of addon menus')
        auto_exploration_group.add_argument('--max-items-per-menu', type=int, default=-1, help='Limit the number of items to explore per menu')
        auto_exploration_group.add_argument('--wait-time', type=float, default=1.0, help='Time to wait between each menu during exploration [1sec]')
        auto_exploration_group.add_argument('--max-items-to-explore', type=int, default=-1, help='Limit the total number of item to explore')
        auto_exploration_group.add_argument('--exploration-strategy', default='RANDOM', choices=['RANDOM', 'FIRST', 'LAST'], help='How to add items of explored menus to the stack to the stack of item to explore')
        auto_exploration_group.add_argument('--max-depth', type=int, default=-1, help='Set the max depth to explore from the entry point')

        cls._config = vars(parser.parse_args())


        config_json = {}

        # We have to check for a config file
        if cls._config['config_file'] != '':
            with open(cls._config['config_file']) as f:
                config_json = json.load(f)

                # Check json dict
                for k in config_json.keys():
                    if k not in cls._config and k != '_comment':
                        raise Exception('The key "{}" in your json file is invalid'.format(k))
                    cls._config[k] = config_json[k]


        # We get the full path of the addon path
        if cls._config['addon_path'] == '':
            raise Exception('You need to specify the path of plugin.video.catchuptvandmore')
        cls._config['addon_path'] = os.path.abspath(cls._config['addon_path'])


        cls._config['addon_id'] = "plugin.video.catchuptvandmore"
        cls._config['addon_fanart_filepath'] = os.path.join(cls._config['addon_path'], 'fanart.jpg')
        cls._config['addon_icon_filepath'] = os.path.join(cls._config['addon_path'], 'icon.png')
        cls._config['addon_en_strings_po_filepath'] = os.path.join(cls._config['addon_path'], "resources", "language", "resource.language.en_gb", "strings.po")


        cls._config['codequick_path'] = os.path.join(CWD_PATH, 'libs', 'script.module.codequick', 'lib')
        cls._config['codequick_addon_path'] = os.path.join(CWD_PATH, 'libs', 'script.module.codequick')
        cls._config['codequick_fanart_filepath'] = os.path.join(cls._config['codequick_addon_path'], 'fanart.jpg')
        cls._config['codequick_icon_filepath'] = os.path.join(cls._config['codequick_addon_path'], 'icon.png')

        cls._config['inputstreamhelper_path'] = os.path.join(CWD_PATH, 'libs', 'script.module.inputstreamhelper', 'lib')
        cls._config['inputstreamhelper_addon_path'] = os.path.join(CWD_PATH, 'libs', 'script.module.inputstreamhelper')
        cls._config['inputstreamhelper_fanart_filepath'] = os.path.join(cls._config['inputstreamhelper_addon_path'], 'fanart.jpg')
        cls._config['inputstreamhelper_icon_filepath'] = os.path.join(cls._config['inputstreamhelper_addon_path'], 'icon.png')

        # Fake Kodi/userdata/addon_data/plugin.video.catchuptvandmore
        cls._config['userdata_path'] = os.path.join(CWD_PATH, 'fake_userdata')


        # We convert the entry point to a list
        entry_point = []
        for item_key in cls._config['entry_point'].split('-'):
            entry_point.append(int(item_key))
        cls._config['entry_point'] = entry_point

        # We move max depth according to the entry point
        if cls._config['max_depth'] != -1:
            cls._config['max_depth'] = cls._config['max_depth'] + len(cls._config['entry_point']) -1


        # Parse settings.xml file
        cls._config['addon_settings'] = {}

        addon_settings_filepath = os.path.join(Config.get('addon_path'), "resources", "settings.xml")
        xml = ET.parse(addon_settings_filepath)
        for child in xml.iter():
            if child.tag == "setting":
                if 'id' in child.attrib:
                    value = ''
                    # print(child.attrib)
                    if child.attrib['type'] == 'folder':
                        value = '/tmp'
                    else:
                        value = child.attrib['default']
                    cls._config['addon_settings'][child.attrib['id']] = value


        cls._config['codequick_fake_settings'] = {}
        cls._config['inputstreamhelper_fake_settings'] = {}


        # Parse english strings.po
        # in order to recover labels
        # Key format: 30500
        # Value format: "France"
        cls._config['addon_labels'] = {}
        po = polib.pofile(Config.get('addon_en_strings_po_filepath'))
        for entry in po:
            key = entry.msgctxt
            key = int(key.replace('#', ''))
            cls._config['addon_labels'][key] = entry.msgid


        cls._config['codequick_labels'] = {
            33078: 'Next page'
        }


        cls._config['inputstreamhelper_labels'] = {}








