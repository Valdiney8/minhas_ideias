# -*- coding: utf-8 -*-

import os
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime
import shutil 
import pandas as pd
from sklearn.cluster import KMeans

class ImageMetaData(object):
   
    image = None
    diretorio_fotos = None
    exif_data = None
    foto = {}
    centroides = {}
    

    def __init__(self, diretorio_fotos, k):
        self.diretorio_fotos = diretorio_fotos
        self.k = k
        self.get_atributos()
       

    def get_atributos(self):
        i = 0
        for r, d, f in os.walk(self.diretorio_fotos):
            for file in f:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    arquivo = os.path.join(r, file)
                    self.image = Image.open(arquivo)
                    lat, lng, alt, data = self.get_lat_lng_alt(arquivo)
                    self.foto[i]={'arquivo': arquivo, 'latitude':lat, 'longitude':lng, 'altitude':alt, 'data':data, 'classe':0}
                    i += 1


    def get_lat_lng_alt(self, arquivo):
        """Returns the latitude and longitude, if available, from the provided exif_data (obtained through get_exif_data above)""" 
        exif_data = {}
        info = self.image._getexif() #info recebe informações cruas do exif. dicionario onde chaves são números ou códigos. data é 36867
        if info:
            for tag, value in info.items(): #separando dicionario em chave e valor ex.: (36867, u'2019:08:14 10:05:30')
                decoded = TAGS.get(tag, tag) #decodifica as chaves. ex.: (36867, u'2019:08:14 10:05:30') é transformado em DateTimeOriginal
                if decoded == "GPSInfo": #verificando se existe informações de gps na imagem
                    gps_data = {} #cria dicionario para armazenar dados do gps
                    for t in value: #para cada valor encontrado no dicionario gps
                        sub_decoded = GPSTAGS.get(t, t) #pega as chaves do dicionario gps
                        gps_data[sub_decoded] = value[t] #armazena o valor de cada chave encontrada no dicionario gps_data
                    exif_data[decoded] = gps_data
                else:
                    exif_data[decoded] = value #se gpsinfo nao existe pega o que existe
        if "GPSInfo" in exif_data:   # existindo gpsinfo no dicionario criado e preenchido   
            gps_info = exif_data["GPSInfo"] #armazena informacoes do gps no novo dicionario gps_info
            gps_altitude = self.get_if_exist(gps_info, "GPSAltitude") #armazena altitude
            alt = gps_altitude[0]/gps_altitude[1]
            gps_latitude = self.get_if_exist(gps_info, "GPSLatitude") #armazena latitude em gps-latitude
            gps_latitude_ref = self.get_if_exist(gps_info, 'GPSLatitudeRef') #verifica a referencia da latitude se sul ou norte
            gps_longitude = self.get_if_exist(gps_info, 'GPSLongitude')
            gps_longitude_ref = self.get_if_exist(gps_info, 'GPSLongitudeRef')
            if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref: 
                lat = self.convert_to_degress(gps_latitude) #manda a latitude para convercao para graus observando a referencia sul ou norte
                if gps_latitude_ref != "N":                     
                    lat = 0 - lat
                lng = self.convert_to_degress(gps_longitude)
                if gps_longitude_ref != "E":
                    lng = 0 - lng
        if "DateTime" in exif_data:
            data_in = exif_data['DateTime']
            data1 = datetime.strptime(data_in, '%Y:%m:%d %H:%M:%S')
            data0 = datetime.strptime("2019:01:01 00:00:00", '%Y:%m:%d %H:%M:%S')
            data = (data1-data0).seconds
        return lat, lng, alt, data


    def get_if_exist(self, data, key):
        if key in data:
            return data[key]
        return None

    def convert_to_degress(self, value):
        """Helper function to convert the GPS coordinates 
        stored in the EXIF to degress in float format"""
        d0 = value[0][0]
        d1 = value[0][1]
        d = float(d0) / float(d1)

        m0 = value[1][0]
        m1 = value[1][1]
        m = float(m0) / float(m1)

        s0 = value[2][0]
        s1 = value[2][1]
        s = float(s0) / float(s1)
        return d + (m / 60.0) + (s / 3600.0)

  
    def mover_foto(self, arquivo, subdiretorio):
        destino = caminho_foto+'/'+str(subdiretorio)
        if not os.path.exists(destino):
            os.makedirs(destino)
        shutil.copy(arquivo, destino)

caminho_foto = '/home/valdiney/Área de Trabalho/Pasta sem título/14.08/todas' 
k = int(input("digite o numero de Pastas e tecle Enter\n"))
sf = ImageMetaData(caminho_foto, k)

a = []
for i in sf.foto:
    a = a + [[sf.foto[i]['latitude'], sf.foto[i]['longitude'], sf.foto[i]['altitude'], sf.foto[i]['data']]]
    
df=pd.DataFrame(a, )
kmeans = KMeans(n_clusters = sf.k, init = 'k-means++')
X = df.iloc[:,0:2]
kmeans.fit(X)
distancias = kmeans.fit_transform(X)
labels = kmeans.labels_

for i in sf.foto:
    sf.mover_foto(sf.foto[i]['arquivo'], labels[i])