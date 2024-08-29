import os
import requests
import matplotlib.pyplot as plt
from datetime import datetime
import pytz
from PIL import Image

class Thingspeak():
    # 從 Thingspeak 獲取數據
    def get_data_from_thingspeak(self, channel_id, api_read_key):
        # 設定 Thingspeak API 的 URL
        url = f'https://thingspeak.com/channels/{channel_id}/feed.json?api_key={api_read_key}'
        # 發送 GET 請求並解析 JSON 數據
        data = requests.get(url).json()
        
        # 如果數據中有 'Not Found' 錯誤，返回錯誤提示
        if data.get('error') == 'Not Found':
            return 'Not Found', 'Not Found'
        
        # 初始化數據列表
        time_list = list()
        bpm_list = list()
        temperature_list = list()
        humidity_list = list()
        body_temperature_list = list()
        ECG_list = list()
        
        # 從數據中提取時間和各個字段的數據
        for data_point in data['feeds']:
            time_list.append(data_point.get('created_at'))
            bpm_list.append(data_point.get('field1'))
            temperature_list.append(data_point.get('field2'))
            humidity_list.append(data_point.get('field3'))
            body_temperature_list.append(data_point.get('field4'))
            ECG_list.append(data_point.get('field5'))

        # 將時間轉換為台灣時間
        tw_time_list = self.format_time(time_list)
        return tw_time_list, bpm_list, temperature_list, humidity_list, body_temperature_list, ECG_list

    # 將時間格式化為台灣時間
    def format_time(self, time_list):
        taiwan_tz = pytz.timezone('Asia/Taipei')  # 台灣時間區域
        tw_time_list = []
        for timestamp in time_list:
            # 解析時間戳
            dt = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')
            # 將 UTC 時間轉換為台灣時間
            dt_utc = pytz.utc.localize(dt)
            dt_taiwan = dt_utc.astimezone(taiwan_tz)
            # 格式化時間
            tw_time_list.append(dt_taiwan.strftime('%Y-%m-%d %H:%M:%S'))
        return tw_time_list

    # 生成圖表
    def gen_chart(self, time_list, field_list, label):
        plt.figure(figsize=(12, 8), dpi=300)  # 設定圖形的大小和解析度
        # 將字段列表中的數據轉換為浮點數，若數據為空或不存在，則設為 0
        field_list = [float(value) if value and value != '' else 0 for value in field_list]
        # 繪製折線圖
        plt.plot(time_list, field_list, 'b-o', label=label)
        plt.xlabel('Time')  # X 軸標籤
        plt.ylabel('Value')  # Y 軸標籤
        plt.title(f'Thingspeak Data - {label}')  # 圖表標題
        plt.xticks(rotation=45)  # X 軸標籤旋轉 45 度
        plt.legend()  # 顯示圖例
        # 設定儲存圖表的文件路徑
        file_path = f'./static/{label}_chart.jpg'
        plt.savefig(file_path, format='jpg')  # 儲存圖表為 JPG 格式
        plt.close()  # 關閉圖形
        return file_path

    # 更新圖片尺寸
    def update_photo_size(self, file_path):
        try:
            img = Image.open(file_path)  # 打開圖片文件
            # 將圖片尺寸調整為 1000x1000 像素
            img_resized = img.resize((1000, 1000))
            resized_file_path = file_path.replace('.jpg', '_resized.jpg')
            img_resized.save(resized_file_path)  # 儲存調整尺寸後的圖片
            return resized_file_path
        except FileNotFoundError:
            print(f"文件 {file_path} 不存在")  # 如果文件不存在，打印錯誤信息
            return None

    # 根據字段生成和上傳圖表
    def process_and_upload_field(self, channel_id, api_read_key, field):
        # 獲取數據
        tw_time_list, bpm_list, temperature_list, humidity_list, body_temperature_list, ECG_list = self.get_data_from_thingspeak(channel_id, api_read_key)
        if tw_time_list == 'Not Found':
            return 'Not Found'
        # 根據字段生成圖表
        if field == 'field1':
            file_path = self.gen_chart(tw_time_list, bpm_list, 'BPM')
        elif field == 'field2':
            file_path = self.gen_chart(tw_time_list, temperature_list, 'temperature')
        elif field == 'field3':
            file_path = self.gen_chart(tw_time_list, humidity_list, 'humidity')
        elif field == 'field4':
            file_path = self.gen_chart(tw_time_list, body_temperature_list, 'body_temperature')
        elif field == 'field5':
            file_path = self.gen_chart(tw_time_list, ECG_list, 'ECG')
        else:
            return 'Invalid Field'

        # 更新圖表圖片尺寸
        resized_file_path = self.update_photo_size(file_path)
        if resized_file_path:
            return {'image_path': resized_file_path}  # 返回圖片的路徑
        else:
            return 'Error Resizing Image'


