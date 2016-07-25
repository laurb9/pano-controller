import json
import re
    
eeprom_idx = 0

def buildMenu(menu, menu_name="menu", title="Main Menu"):
    output = []
    menus = []
    eeprom_map = []
    global eeprom_idx

    for i, menu_item in enumerate(menu):
        menu_item_name = "menu_" + re.sub(r"[^\w]", "_", menu_item["description"].lower())
        menu_item["name"] = menu_item_name
        output.append("// %(description)s" % menu_item)
        if "variable" in menu_item:
            output.append("extern volatile int %(variable)s;" % menu_item)
            menu_item["variable"] = "&%s" % menu_item["variable"]
        else:
            menu_item["variable"] = "NULL"
            menu_item["default"] = 0
            menu_item.pop("eeprom", "")

        if "onselect" in menu_item:
            output.append("int %s(int);" % menu_item["onselect"])
        else:
            menu_item["onselect"] = "NULL";
        
        if menu_item.get("eeprom"):
            eeprom_idx += 1;
            menu_item["eeprom"] = eeprom_idx
        else:
            menu_item["eeprom"] = 0

        names = []
        values = []
        default_val = 0
        if "menu" not in menu_item:
            output.append('static const PROGMEM char %(name)s_desc[] = "%(description)s";' % menu_item)
        
        if "options" in menu_item:
            if isinstance(menu_item["options"][0], dict):
                for j, option in enumerate(menu_item["options"]):
                    name, value = option.items()[0]
                    if menu_item["default"] == name:
                        default_val = value
    
                    var_name = "%s_name_%d" % (menu_item_name, j)
                    output.append('static const PROGMEM char %s[] = "%s";' % (var_name, name))
                    names.append(var_name)
                    values.append(str(value))
                    
                menu_item["names"] = ", ".join(names)
                output_fmt = """
static const PROGMEM char * const %(name)s_names[%(size)d] = {%(names)s};
static const PROGMEM int %(name)s_values[%(size)d] = {%(values)s};
static NamedListSelector %(name)s(%(name)s_desc, %(variable)s, %(default_val)d, %(eeprom)d * sizeof(int), %(onselect)s, %(size)d, %(name)s_names, %(name)s_values);
"""
            else:
                for j, value in enumerate(menu_item["options"]):
                    if menu_item["default"] == value:
                        default_val = value
    
                    values.append(str(value))

                output_fmt = """
static const PROGMEM int %(name)s_values[%(size)d] = {%(values)s};
static ListSelector %(name)s(%(name)s_desc, %(variable)s, %(default_val)d, %(eeprom)d * sizeof(int), %(onselect)s, %(size)d, %(name)s_values);
"""
            menu_item["default_val"] = default_val
            menu_item["size"] = len(values)
            menu_item["values"] = ", ".join(values)
            output.append(output_fmt % menu_item)
        
        elif "step" in menu_item:
            output.append(
"""
static RangeSelector %(name)s(%(name)s_desc, %(variable)s, %(default)d, %(eeprom)d * sizeof(int), %(onselect)s, %(min)d, %(max)d, %(step)d);
""" % menu_item)
            
        elif "menu" in menu_item:
            output += buildMenu(menu_item["menu"], menu_name=menu_item_name, title=menu_item["description"])
            
        else:
            output.append(
"""
static OptionSelector %(name)s(%(name)s_desc, %(variable)s, %(default)d, %(eeprom)d * sizeof(int), %(onselect)s);
""" % menu_item)
        
        menus.append(menu_item_name)
        

    output.append(
"""
static const PROGMEM BaseMenu * %s_opts[] = {&%s};
static const PROGMEM char %s_desc[] = "%s";
Menu %s(%s_desc, %d, %s_opts);
""" % (menu_name, ", &".join(menus), 
       menu_name, title, 
       menu_name, menu_name, len(menus), menu_name))

    return output

if __name__ == "__main__":
    output = ["""
/*
 * Do not edit this file, it is autogenerated.
 * Edit menu_cfg.json instead, then type "make".
 */
#include "menu.h"
"""]

    with open("menu_cfg.json") as f:
        menu = json.load(f)

    output += buildMenu(menu, title="Main Menu")
    print "\n".join(output)
