import pandas as pd
import qrcode


def image_generator(csv_file_path):
    df = pd.read_csv(csv_file_path, usecols=['employee_name', 'equipment_name', 'equipment_id'])
    for i in range(len(df)):
        df1=df.loc[i, :]
        df_list = df1.values.tolist()
        df_list = ', '.join(map(str, df_list))
        qr = qrcode.QRCode()
        qr.add_data(df_list)
        qr.make()
        img = qr.make_image()
        file_name = df["employee_name"][i]
        img.save(file_name+'.png')

if __name__ == "__main__":
    csv_file_path = "test_data.csv"
    image_generator(csv_file_path)