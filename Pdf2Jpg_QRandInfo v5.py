import glob
import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import pyzbar.pyzbar as pyzbar
import easyocr
import numpy as np

#region 调参
# 文件输入
input_folder = '/Users/songwang/Desktop/Python/testcases/20240314'
# input_folder = 'C:/Users/WangSong/OneDrive/Python/testcases'

# 手动输入日期
date_today = '2024.3.14'

# 新图参数
img_dst_width = 750
img_dst_height = 710
img_dst_filename_temp = '/temp.jpg'

# 新图的坐标系，起始点
coordinate_dst_qr       = (326, 33)
coordinate_dst_title    = (27, 429)
coordinate_dst_person   = (28, 533)
coordinate_dst_date     = (28, 581)
coordinate_dst_qrtext   = (27, 632)

#字体相关
font_style_title = '/System/Library/Fonts/ヒラギノ角ゴシック w3.ttc'
font_style_kanji = '/System/Library/Fonts/ヒラギノ角ゴシック w6.ttc'
font_style_date = 'Aileron-bold.otf'
# font_style_qrtext = '/System/Library/Fonts/supplemental/arial.ttf'
font_style_qrtext = 'Aileron-black.otf'

#endregion

#region 环境
    # brew install python
    # brew install pyzbar
    # brew install easyocr
#endregion

#region 方法
def AddMarkToEndOfFilename(file_path, mark, newfile_ext):
    folderpath, filename = os.path.split(file_path)             # 分离文件夹路径，文件名
    newfile_path = folderpath + '/' + filename + mark           # 新文件名

    flag = False
    while os.path.exists(newfile_path + newfile_ext):           # 判断此文件是否已经存在，存在则文件名后面添加字符串
        newfile_path = newfile_path + '~1'                      # 如果存在则一直增加此字符串
        flag = True

    if flag == True:                                            # print，发现重复文件
        print('***Duplicate file found*** ' + filename)

    os.rename(file_path, newfile_path + newfile_ext)            # 重命名

def GetQrPos(file_path):
    """
    convert('L'): 灰度图
    point( lambda p: 255 if p > 30 else 0 )：像素点超过30则255，否则0
    convert('1')：二值化
    """
    img = Image .open(file_path)\
                .convert('L')\
                .point( lambda p: 255 if p > 30 else 0 )\
                .convert('1')
    barcodes = pyzbar.decode(img)
    if (len(barcodes) == 0): return False
    else:                    return barcodes[0].rect

def GetBackgroundImage(text):
    if text == '東京ディズニーシー':
        return Image.open('background_sea.jpg')
    elif text == '東京ディズニーランド':
        return Image.open('background_land.jpg')
    else:
        return False

def GetDateText(text):
    year = month = day = ''

    for index in range(len(text)):
        if text[index] == '年':
            year = text[index-4:index]
        if text[index] == '月':
            if text[index-2] == '年': month = text[index-1:index]
            else:                     month = text[index-2:index]
        if text[index] == '日':
            if text[index-2] == '月': day = text[index-1:index]
            else:                     day = text[index-2:index]
    
    if year == '' or month == '' or day == '': return False
    else: return year + '.' + month + '.' + day

def FormatTitle(text):
    text = text.replace('1 ', '１')

    for index in range(len(text)):
        if text[index] == ' ': return text[0:index]
#endregion

#region Main
input_files = glob.glob(os.path.join(input_folder, '*.png'))

count_png = 0
count_png_fail = 0

reader = easyocr.Reader(['ja', 'en'])

for input_file_path in input_files:

    is_done = True

    img_src = Image.open(input_file_path).convert('L')
    img_dst = Image.new('RGB', (img_dst_width, img_dst_height), '#FFF')
    draw = ImageDraw.Draw(img_dst)

    # 获取QR位置
    # rect[0]: x, rect[1]: y, rect[2]: width, rect[3]: height
    rect = GetQrPos(input_file_path)

    if rect == False:
        is_done = False
    else:
        
        # 除去QR，截取文字部分
        # 简单预处理，提高识别率
        img_text = img_src.crop((0, rect[1] + rect[3], img_src.size[0], img_src.size[1]))
        enhancer= ImageEnhance.Contrast(img_text)
        img_text = enhancer.enhance(2.0)

        # 读出所有文字
        result = reader.readtext(np.array(img_text), detail = 0)

        if (len(result) != 6):
            is_done = False

        else:
            # 根据sea or land取得背景
            img_bg = GetBackgroundImage(result[3])

            if img_bg == False:
                is_done = False

            else:
                # 贴背景
                img_dst.paste(img_bg, (0, 0))

                # 贴QR
                img_dst.paste(img_src.crop((rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3])).resize((97, 97)), coordinate_dst_qr)

                # 贴Title
                font = ImageFont.truetype(font = font_style_title, size = 22)
                draw.text(coordinate_dst_title, FormatTitle(result[0]) + '◆', font = font, fill = '#083962')

                # 贴大小人
                font = ImageFont.truetype(font = font_style_kanji, size = 28)
                draw.text(coordinate_dst_person, result[1], font = font, fill = '#083962')

                # 贴日期
                date_text = date_today

                font = ImageFont.truetype(font = font_style_date, size = 28)
                draw.text(coordinate_dst_date, date_text, font = font, fill = '#083962')

                # 贴QR数字
                font = ImageFont.truetype(font = font_style_qrtext, size = 20)
                draw.text(coordinate_dst_qrtext, result[4], font = font, fill = '#8A96AF')
                
                img_dst.save(input_folder + '/' + result[4] + '.jpg', 'JPEG', optimize=True, quality = 100)

                count_png += 1

    if is_done == False: 
        AddMarkToEndOfFilename(input_file_path, '_Fail_' + str(count_png_fail), '.jpg')
        count_png_fail += 1


print(str(count_png) + ' PNG file(s) processed')
print(str(count_png_fail) + ' PNG file(s) failed')
#endregion