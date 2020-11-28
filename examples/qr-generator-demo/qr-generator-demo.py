import pandas as pd
import qrcode
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

def image_generator(csv_file_path):
    df = pd.read_csv(csv_file_path, usecols=['employee_name', 'equipment_name', 'equipment_id'])

    for i in range(len(df)):
        df_list = df.loc[i, :].values.tolist()
        df_list = ', '.join(map(str, df_list))
        qr = qrcode.QRCode()
        qr.add_data(df_list)
        qr.make()

        img = qr.make_image()
        draw = ImageDraw.Draw(img)
        x = 140
        y = 10
        draw.text((x, y), df["employee_name"][i], font=ImageFont.load_default())
        file_name = df["employee_name"][i]
        img.save(file_name + '.png')

if __name__ == "__main__":

    csv_file_path = "test_data.csv"
    image_generator(csv_file_path)
