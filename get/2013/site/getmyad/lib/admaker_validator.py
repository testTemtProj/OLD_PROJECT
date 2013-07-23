# encoding: utf-8
from schema_validator import *

Int = Integer(allow_convert=True)
Color = Regex("[0-9a-fA-F]{6}$", default="777777")
PixelSize = Regex("\d+\s?px$", default="100%") # TODO: нужен ли default?
Position = String(one_of=["bottom-right", "top-right",
                          "bottom-left", "top-left"])
FontFamily = String(default='Arial, "Helvetica CY",  sans-serif')     # TODO: one_of

Block = {
        "borderColor": Color,
        "borderWidth": Integer(allow_convert=True, default=0),
        "fontUnderline": Boolean,
        "borderColorStatus": Boolean(default=False),
        "backgroundColorStatus": Boolean(default=False),
        "fontBold": Boolean,
        "fontFamily": FontFamily,
        "fontSize": Integer(allow_convert=True, default=10),
        "hide": Boolean,
        "top": Int,
        "left": Int,
        "height": PixelSize,
        "width": PixelSize,
        "align": String(one_of=["center", "left", "right"], default="center")
}

MainBlock = Block.copy()
MainBlock["itemsNumber"] = Int
MainBlock["backgroundColor"] = Color

TextBlock = Block.copy()
TextBlock['fontColor'] = Color

admaker_schema = {
    "Description": TextBlock,
    "Image": Block,
    "Header": TextBlock,
    "Cost": TextBlock,
    "Advertise": Block,
    "Main": MainBlock,
    "Nav": {
        "logoHide": Boolean(default=False),
        "color": Color,
        "logoColor": String(one_of=["color", "blue", "black", "white"]),
        "logoPosition": Position,
        "navPosition": Position,
        "backgroundColor": Color,
        "hovercolor": Color
    }
}

def _mix_colors(color1, color2):
    ''' Смешивает цвета ``color1`` и ``color2``.

        Цвета передаются в формате rrggbb, в таком же формате возвращается
        результат.
    '''
    def split_rgb(c):
        split = (c[0:2], c[2:4], c[4:6])
        return [int(x, 16) for x in split]

    c1 = split_rgb(color1)
    c2 = split_rgb(color2)
    mixed = [(x[0] + x[1]) / 2 for x in zip(c1, c2)]
    return ''.join(hex(x)[2:] for x in mixed)

def validate_admaker(admaker_options):
    ''' Выполняет проверку настроек admaker.

        Возвращает корректный объект (с исправленными некритичными полями).
        Бросает ValidationError в случае серьёзных нарушений схемы. '''
    validated = validate(admaker_options, admaker_schema)
    validated['Nav']['hovercolor'] = _mix_colors(validated['Nav']['color'],
                                                 validated['Nav']['backgroundColor'])

    return validated

__all__ = ['validate_admaker']
