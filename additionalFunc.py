# Некоторые вспомогательные функции для подготовки для записи в базу

import fleep
import os.path
import hashlib
import querys
import shutil

ABSOLUTE_FILE_PATH_DST = '/home/user/Documents/MGTSounds/2020.07.10/dst/'
ABSOLUTE_FILE_PATH_SRC = '/home/user/Documents/MGTSounds/2020.07.10/src/'
ABSOLUTE_FILE_PATH_ID = '/home/user/Documents/MGTSounds/2020.07.10/id/'

# Подсчитывает контрольную сумму файла
def audio_crc(file_path: str):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()


# Подгатавливает аудиофайл к записи, считает контрольную сумму, длительность, определяет тип файла
# Тут querys.NAME - хекс представление имени файла, и лезем мы за ним в dest
def prepare_audio_to_write(audio_info: list):
    result = []

    for el in audio_info:

        extension = None

        if os.path.isfile(ABSOLUTE_FILE_PATH_DST + el[querys.NAME] + '.mp3'):
            extension = '.mp3'
        elif os.path.isfile(ABSOLUTE_FILE_PATH_DST + el[querys.NAME] + '.wav'):
            extension = '.wav'
        else:
            print('Не найден файл {} для остановки {}'.format(ABSOLUTE_FILE_PATH_DST + el[querys.NAME], el[querys.STOP_ID]))
            continue

        with open(ABSOLUTE_FILE_PATH_DST + el[querys.NAME] + extension, 'rb') as f:
            info = fleep.get(f.read(128))

        file_type = info.mime[0] if len(info.mime) != 0 else ''

        result.append({'duration': 1, 'crc': audio_crc(ABSOLUTE_FILE_PATH_DST + el[querys.NAME] + extension),
                       'file_type': file_type,
                       'description': el[querys.SOURCE_NAME], 'file_name': el[querys.NAME] + extension})

    return result


# Проверяет существует ли аудиофайл к маршруту и возвращает список:
# - route_id
# - route_human_name
# - sound_source_name
def find_audio_to_route(route_without_audio: tuple):
    result = []
    prefix = 'М-т '
    mp3 = '.mp3'
    wav = '.wav'
    for route_name, route_id in route_without_audio:
        if os.path.isfile(ABSOLUTE_FILE_PATH_SRC + prefix + route_name + mp3):
            result.append({'route_id': route_id, 'route_human_name': route_name,
                           'sound_source_name': os.path.basename(ABSOLUTE_FILE_PATH_SRC + prefix + route_name + mp3)})
        elif os.path.isfile(ABSOLUTE_FILE_PATH_SRC + prefix + route_name + wav):
            result.append({'route_id': route_id, 'route_human_name': route_name,
                           'sound_source_name': os.path.basename(ABSOLUTE_FILE_PATH_SRC + prefix + route_name + wav)})

    print('Find {} audio to route'.format(len(result)))

    return result

 # audio_names - список после запроса
    # [0] - имя в sound/dst
    # [1] - name from sound/src
    # [2] - sound_id
    # [3] - route_id
    # [4] - route_name
def prepare_route_audio_to_write(route_audio_info):
    result = []

    for el in route_audio_info:
        extension = None

        if os.path.isfile(ABSOLUTE_FILE_PATH_DST + el[0] + '.mp3'):
            extension = '.mp3'
        elif os.path.isfile(ABSOLUTE_FILE_PATH_DST + el[0] + '.wav'):
            extension = '.wav'
        else:
            print('Не найден файл ', ABSOLUTE_FILE_PATH_DST + el[querys.NAME])
            continue

        with open(ABSOLUTE_FILE_PATH_DST + el[0] + extension, 'rb') as f:
            info = fleep.get(f.read(128))

        file_type = info.mime[0] if len(info.mime) != 0 else ''

        result.append({'duration': 1, 'crc': audio_crc(ABSOLUTE_FILE_PATH_DST + el[querys.NAME] + extension),
                       'file_type': file_type,
                       'description': el[querys.SOURCE_NAME], 'file_name': el[querys.NAME] + extension})

    return result



# Переименовываввет аудио маршрута в sha256, это надо проделывать только с аудио маршрутов
# TODO: хотя тут надо подумать, как то не совсем универсально выходит, через жопку
def rename_route_audio(audios_name):
    for audio_source_name in audios_name:
        audio_dst_name = audio_crc(ABSOLUTE_FILE_PATH_SRC + audio_source_name)
        if os.path.exists(ABSOLUTE_FILE_PATH_DST + audio_dst_name):
            print(audio_dst_name, 'file already exist')
        else:
            print('Copy file: ', ABSOLUTE_FILE_PATH_DST + audio_dst_name)
            shutil.copy(ABSOLUTE_FILE_PATH_SRC + audio_source_name,
                        ABSOLUTE_FILE_PATH_DST + audio_dst_name)


# Данная функция копирует в отдельную папку аудио файлы со следующим названием: <id>.<dst_name>
def set_id_to_audio_name(audios_name_with_id):
    #[0] - dst папка и имя файла там
    #[1] - file_id from db
    for audio_source_name in audios_name_with_id:
        extension = ""
        source_name = audio_source_name[0]
        print('Source_name: ', source_name)
        if os.path.exists(ABSOLUTE_FILE_PATH_DST + source_name + '.wav'):
            extension = '.wav'
            source_name += extension
        elif os.path.exists(ABSOLUTE_FILE_PATH_DST + source_name + '.mp3'):
            extension = '.mp3'
            source_name += extension
        elif os.path.exists(ABSOLUTE_FILE_PATH_DST + source_name):
            print('Find file {} without extension'.format(source_name))
        else:
            print('Cant find audiofile: ', source_name)
            continue

        dst_file_name_arr = str(audio_source_name[0]).split(" ")
        separator = "_"
        file_name = separator.join(dst_file_name_arr)

        audio_dst_name = str(ABSOLUTE_FILE_PATH_ID) + str(audio_source_name[1]) + '.' + file_name

        if os.path.exists(audio_dst_name):
            print(audio_dst_name, 'file already exist')
        else:
            print('Copy file {} to {}'.format(ABSOLUTE_FILE_PATH_DST + source_name,
                                              audio_dst_name))
            shutil.copy(ABSOLUTE_FILE_PATH_DST + source_name,
                        audio_dst_name)


# Формирует аудиошаблон и возвращает мапу:
def create_template(name: str, description: str):
    result = {'name': name, 'description': description, 'comments': None, 'category': None,
              'dt_start': None, 'dt_end': None}
    return result


# Убираем из описания маршрута технические остановки и все, что с ними связано
def prepare_route_description(route_description: dict):
    result = {}

    for trip in route_description:
        obj = route_description[trip]

        # если начало - технологическое, а за ним - посадка - выкидываем начало
        if obj['stops_mod'][0] == 6 and obj['stops_mod'][1] == 2:
            obj['stops_mod'].pop(0)
            obj['stops_id'].pop(0)
            obj['stops_seq'].pop(0)
            obj['id'].pop(0)
        # Иначе назначаем, что первая остановка - посадка
        elif obj['stops_mod'][0] == 6 or obj['stops_mod'][0] == 1:
            obj['stops_mod'][0] = 2

        # Если конец тезнологический, а перед ним высадка - выкидываем конец
        if obj['stops_mod'][len(obj['stops_mod']) - 1] == 6 and obj['stops_mod'][len(obj['stops_mod']) - 2] == 3:
            obj['stops_mod'].pop(len(obj['stops_mod']) - 1)
            obj['stops_id'].pop(len(obj['stops_mod']) - 1)
            obj['stops_seq'].pop(len(obj['stops_mod']) - 1)
            obj['id'].pop(len(obj['id']) - 1)
        elif obj['stops_mod'][len(obj['stops_mod']) - 1] == 6:
            obj['stops_mod'][len(obj['stops_mod']) - 1] = 3

        result['trip_{}'.format(trip)] = obj

    return result
