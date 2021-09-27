
import psycopg2
import querys
import additionalFunc
from names import *

DEPOT_ID = 116

DJINGL_SOUND = "_Джингл"
MGT_SOUND = "_МГТ"
SLED_DO_SOUND = "_А следует"
TO_STATION_SOUND = "_А до ост."
NEXT_STATION_SOUND = "_След. ост."
GOOD_TRIP_SOUND = "_Приятной поездки"
FINITE_SOUND = "_Конечная"
GOODBY_SOUND = "_Прощание"
EXTENSION = ".wav"

TEXT_SEPARATOR = '#!#'

class source_db:
    def __init__(self):
        self.conn = None

    def connect(self):
        # Connect to adcs_mgt PostgreSQL server
        self.conn = psycopg2.connect(
            host="kiask-farm-01.kiask.ru",
            database="adcs_mgt",
            user="postgres",
            password="postgres",
            port="5432"
        )

        # create a cursor

        cur = self.conn.cursor()

        # execute a statement
        cur.execute("SELECT version();")
        print('Source PostgreSQL database version:', cur.fetchone())

    def get_sound_source_per_station(self):
        result = None

        with self.conn.cursor() as curs:
            curs.execute(querys.SOUND_PER_STATION, (DEPOT_ID,))
            print('Get sound resources per station query: ', curs.query)
            result = curs.fetchall()

        return result

    def get_sound_per_route(self):
        result = None

        with self.conn.cursor() as curs:
            curs.execute(querys.GET_SOUND_ON_ROUTE_FROM_SOURCE, (DEPOT_ID,))
            print('Get sound per route from source: ', curs.query)
            result = curs.fetchall()

        return result

    def get_stops_with_text_resources(self):
        result = None

        with self.conn.cursor() as curs:
            curs.execute(querys.GET_STOPS_WITH_TEXT_FROM_SOURCE, (DEPOT_ID,))
            print('Get stops with text resources: ', curs.query)
            result = curs.fetchall()

        return result

    def get_routes_with_text_resources(self):
        result = None

        with self.conn.cursor() as curs:
            curs.execute(querys.GET_ROUTE_WITH_TEXT_FROM_SOURCE, (DEPOT_ID,))
            print('Get routes with text resources: ', curs.query)
            result = curs.fetchall()

        return result

    def get_trips_with_text_resources(self):
        result = None

        with self.conn.cursor() as curs:
            curs.execute(querys.GET_TRIP_WITH_TEXT_RESOURCES_FROM_SRC, (DEPOT_ID,))
            print('Get trips with text resources: ', curs.query)
            result = curs.fetchall()

        return result


class dist_db:
    def __init__(self):
        self.conn = None
        self.text_template_id = -1
        self.text_value_id = -1

    def connect(self):
        # Connect to adcs_mgt PostgreSQL server
        self.conn = psycopg2.connect(
            host="192.168.85.21",
            database="adcs_mgt",
            user="postgres",
            password="postgres",
            port="5432"
        )

        self.conn.autocommit = True

        # create a cursor
        cur = self.conn.cursor()

        # execute a statement
        cur.execute("SELECT version();")
        print('Dest PostgreSQL database version:', cur.fetchone())

    # Функция, которая добавляет аудиофайлы в таблицу tbl_file, а также привязывает звуки к станциям
    def connect_audio_to_station(self, source_audio_per_station):
        stop_with_audio_to_add_list = []

        with self.conn.cursor() as curs:
            # Достаем список аудио из dest базы, у которых уже есть звуки (а именно 2 привязанных)
            curs.execute(querys.GET_STOP_AUDIO_FROM_DIST, (DEPOT_ID,))
            dest_stopid_with_audio_tuple = curs.fetchall()
            dest_stopid_with_audio_list = []

        # Формируем список из id остановок, у которых уже есть привязанные звуки
        for el in source_audio_per_station:
            print("Stop with audio from src", el[querys.STOP_ID])

        for el in dest_stopid_with_audio_tuple:
            print("Stop with audio from dst", el[0])
            dest_stopid_with_audio_list.append(el[0])


        # Проверим, какие станции с привязанными звуками из source базы отсутствуют в dest базе
        # TODO: если есть хоть один такой id, хоть с одним привязанным звуком, то никакой другой звук не добавляется ну короче ебала какая то тут
        for el in source_audio_per_station:
            if el[querys.STOP_ID] not in dest_stopid_with_audio_list:
                print('Find stop without audio stop_id ', el[querys.STOP_ID])
                stop_with_audio_to_add_list.append(el)

        #for stop_info in stop_with_audio_to_add_list:
            #print('stop_id: ', stop_info[querys.STOP_ID])

        # Сформировали данные для записи аудиофайла в tbl_file

        tbl_file_audio_info = additionalFunc.prepare_audio_to_write(stop_with_audio_to_add_list)

        self.add_audio_to_tbl_file(tbl_file_audio_info)

        with self.conn.cursor() as curs:
            audio_with_stop_id = []

            # Собираем stop_id и audio_id для того, чтобы это все записать в базу
            for el in stop_with_audio_to_add_list:
                curs.execute(querys.GET_AUDIO_ID_BY_DESCRIPTION, (el[querys.SOURCE_NAME],))
                audio_id = curs.fetchall()

                if len(audio_id[0]) != 0:
                    audio_with_stop_id.append({'stop_id': el[querys.STOP_ID], 'audio_id': audio_id[0][0]})

            # Собственно запись в базу
            for el in audio_with_stop_id:
                try:
                    print('Insert audio {} to station {}'.format(el['audio_id'], el['stop_id']))
                    curs.execute(querys.INSERT_INTO_TBL_STATION_AUDIO, (el['stop_id'], el['audio_id']))
                except psycopg2.errors.UniqueViolation as err:
                    print('Error: ', err)
                    continue
                except psycopg2.errors.ForeignKeyViolation as err:
                    print('Error: ', err)
                    continue

    def add_audio_to_tbl_file(self, audios_resources):
        with self.conn.cursor() as curs:
            audios_with_id = []
            for prepared_audio in audios_resources:
                # file_name - название файла в папке dst
                # description - мальное описание файла

                file_name_arr = prepared_audio['file_name'].split(" ")
                separator = "_"
                file_name = separator.join(file_name_arr)

                curs.execute(querys.ADD_AUDIO_TO_DEST, (prepared_audio['description'], file_name,
                                                        prepared_audio['file_type'], prepared_audio['crc']))

                audio_id = curs.fetchall()[0][0]
                audios_with_id.append([prepared_audio['file_name'], audio_id])

            additionalFunc.set_id_to_audio_name(audios_with_id)
    # source_route_with_audio - список после запроса
    # [0] - имя в sound/dst
    # [1] - name from sound/src
    # [2] - sound_id
    # [3] - route_id
    # [4] - route_name
    def connect_audio_to_route(self, source_route_with_audio):
        print('len of source route with audio {}'.format(len(source_route_with_audio)))
        route_with_audio_to_add_to_dest = []
        route_with_audio_from_dest = []
        # Вытащим список маршрутов, у которых есть привязанные звуки
        # [0] - route_short_name
        # [1] - route_id
        with self.conn.cursor() as curs:
            curs.execute(querys.GET_ROUTE_WITH_AUDIO_FROM_DEST, (DEPOT_ID,))
            route_with_audio_from_dest_tuple = curs.fetchall()
            print('Find {} routes with audio'.format(len(route_with_audio_from_dest_tuple)))

        for info in route_with_audio_from_dest_tuple:
            route_with_audio_from_dest.append(info[1])

        #Составим список маршрутов из исходной базы, которых нет в итоговой
        print('route with audio from dest len ', len(route_with_audio_from_dest))
        for info in source_route_with_audio:
            if info[3] not in route_with_audio_from_dest:
                print('route {} doesnt exist in dest base'.format(info[3]))
                route_with_audio_to_add_to_dest.append(info)
            else:
                print('route {} exist in dest base'.format(info[3]))

        print("======================================================")
        print("======================================================")
        print("======================================================")
        print("======================================================")
        print("======================================================")
        print("СФОРМИРОВАЛИ СПИСОК МАРШРУТОВ СО ЗВУКАМИ НА ДОБАВЛЕНИЕ")
        print('Количество маршрутов ', len(route_with_audio_to_add_to_dest))
        print("======================================================")
        print("======================================================")
        print("======================================================")
        print("======================================================")
        print("======================================================")
        for route_id in route_with_audio_to_add_to_dest:
            print('Route id: ', route_id[3])

        prepared_audio_to_dest = additionalFunc.prepare_route_audio_to_write(route_with_audio_to_add_to_dest)
        self.add_audio_to_tbl_file(prepared_audio_to_dest)

        with self.conn.cursor() as curs:
            audio_with_route_id = []

            # Собираем stop_id и audio_id для того, чтобы это все записать в базу
            for el in route_with_audio_to_add_to_dest:
                curs.execute(querys.GET_AUDIO_ID_BY_DESCRIPTION, (el[querys.SOURCE_NAME],))
                audio_id = curs.fetchall()

                if len(audio_id[0]) != 0:
                    audio_with_route_id.append({'route_id': el[querys.STOP_ID], 'audio_id': audio_id[0][0]})

            # Собственно запись в базу
            for el in audio_with_route_id:
                try:
                    print('Insert audio {} to route {}'.format(el['audio_id'], el['route_id']))
                    curs.execute(querys.INSERT_INTO_TBL_ROUTE_AUDIO, (el['route_id'], el['audio_id']))
                except psycopg2.errors.UniqueViolation as err:
                    print('Error: ', err)
                    continue
                except psycopg2.errors.ForeignKeyViolation as err:
                    print('Error: ', err)
                    continue


    # TODO: предусмотреть, что это должно использоваться один раз по сути
    def create_audio_template(self):
        # Шаблон под начальные остановки
        first_station_template = additionalFunc.create_template('Начальная', 'Аудиошаблон на начальную остановку')
        pre_finite_station_template = additionalFunc.create_template('Предпоследняя',
                                                                     'Аудиошаблон на предпоследнюю остановку')
        finite_station_template = additionalFunc.create_template('Конечная', 'Аудиошаблон на конечную остановку')
        station_template = additionalFunc.create_template('Остановка',
                                                          'Аудиошаблон на остановки, кроме начальной, предпоследней и конечной')

        with self.conn.cursor() as curs:
            curs.execute(querys.INSERT_AUDIO_TBL_TEMPLATE,
                         (first_station_template['name'], first_station_template['description']))
            first_station_template_id = curs.fetchall()[0][0]

            curs.execute(querys.INSERT_AUDIO_TBL_TEMPLATE,
                         (pre_finite_station_template['name'], pre_finite_station_template['description']))
            pre_finite_station_template_id = curs.fetchall()[0][0]

            curs.execute(querys.INSERT_AUDIO_TBL_TEMPLATE,
                         (finite_station_template['name'], finite_station_template['description']))
            finite_station_template_id = curs.fetchall()[0][0]

            curs.execute(querys.INSERT_AUDIO_TBL_TEMPLATE,
                         (station_template['name'], station_template['description']))
            station_template_id = curs.fetchall()[0][0]

        # Формиурем список аудио на шаблон
        first_station_audio_template = []
        pre_finite_station_audio_template = []
        finite_station_audio_template = []
        station_audio_template = []

        with self.conn.cursor() as curs:
            # Собираем ресурсы для начальной остановки
            first_station_audio_template.append({'resources': {'id_entity': first_station_template_id,
                                                               'id_audio_file': self.get_audio_id_by_file_name(
                                                                   DJINGL_SOUND + EXTENSION),
                                                               'event_type': 'AFTERSTATION', 'sorting': 1, 'pause': 0}})

            first_station_audio_template.append({'resources': {'id_entity': first_station_template_id,
                                                               'id_audio_file': self.get_audio_id_by_file_name(
                                                                   MGT_SOUND + EXTENSION),
                                                               'event_type': 'AFTERSTATION', 'sorting': 2, 'pause': 0}})

            first_station_audio_template.append({'resources': {'id_entity': first_station_template_id,
                                                               'id_audio_file': self.get_audio_id_by_file_name(
                                                                   SLED_DO_SOUND + EXTENSION),
                                                               'event_type': 'AFTERSTATION', 'sorting': 3, 'pause': 0}})

            first_station_audio_template.append(
                {'substitution': {'id_template': first_station_template_id, 'substitution_code': 'ROUTE_NUM',
                                  'substitution_file_type': 'FEMALE_SOUND', 'sorting': 4, 'pause': 0,
                                  'event_type': 'AFTERSTATION'}})

            first_station_audio_template.append({'resources': {'id_entity': first_station_template_id,
                                                               'id_audio_file': self.get_audio_id_by_file_name(
                                                                   TO_STATION_SOUND + EXTENSION),
                                                               'event_type': 'AFTERSTATION', 'sorting': 5, 'pause': 0}})

            first_station_audio_template.append({'substitution': {'id_template': first_station_template_id,
                                                                  'substitution_code': 'END_STOP',
                                                                  'substitution_file_type': 'FEMALE_SOUND',
                                                                  'sorting': 6,
                                                                  'pause': 0, 'event_type': 'AFTERSTATION'}})

            first_station_audio_template.append({'resources': {'id_entity': first_station_template_id,
                                                               'id_audio_file': self.get_audio_id_by_file_name(
                                                                   NEXT_STATION_SOUND + EXTENSION),
                                                               'event_type': 'AFTERSTATION', 'sorting': 7, 'pause': 0}})

            first_station_audio_template.append({'substitution': {'id_template': first_station_template_id,
                                                                  'substitution_code': 'NEXT_STOP',
                                                                  'substitution_file_type': 'FEMALE_SOUND',
                                                                  'sorting': 8,
                                                                  'pause': 0, 'event_type': 'AFTERSTATION'}})

            first_station_audio_template.append({'resources': {'id_entity': first_station_template_id,
                                                               'id_audio_file': self.get_audio_id_by_file_name(
                                                                   GOOD_TRIP_SOUND + EXTENSION),
                                                               'event_type': 'AFTERSTATION', 'sorting': 9, 'pause': 0}})

            # Конечная станция
            finite_station_audio_template.append({'resources': {'id_entity': finite_station_template_id,
                                                                'id_audio_file': self.get_audio_id_by_file_name(
                                                                    DJINGL_SOUND + EXTENSION),
                                                                'event_type': 'BEFORESTATION', 'sorting': 1,
                                                                'pause': 0}})

            finite_station_audio_template.append({'resources': {'id_entity': finite_station_template_id,
                                                                'id_audio_file': self.get_audio_id_by_file_name(
                                                                    FINITE_SOUND + EXTENSION),
                                                                'event_type': 'BEFORESTATION', 'sorting': 2,
                                                                'pause': 0}})

            finite_station_audio_template.append({'resources': {'id_entity': finite_station_template_id,
                                                                'id_audio_file': self.get_audio_id_by_file_name(
                                                                    GOODBY_SOUND + EXTENSION),
                                                                'event_type': 'BEFORESTATION', 'sorting': 3,
                                                                'pause': 0}})

            # Аудиошаблон на предпоследнюю остановку
            pre_finite_station_audio_template.append({'resources': {'id_entity': pre_finite_station_template_id,
                                                                    'id_audio_file': self.get_audio_id_by_file_name(
                                                                        DJINGL_SOUND + EXTENSION),
                                                                    'event_type': 'BEFORESTATION', 'sorting': 1,
                                                                    'pause': 0}})

            first_station_audio_template.append({'substitution': {'id_template': pre_finite_station_template_id,
                                                                  'substitution_code': 'THIS_STOP',
                                                                  'substitution_file_type': 'FEMALE_SOUND',
                                                                  'sorting': 2,
                                                                  'pause': 0, 'event_type': 'BEFORESTATION'}})

            station_audio_template.append({'resources': {'id_entity': pre_finite_station_template_id,
                                                         'id_audio_file': self.get_audio_id_by_file_name(
                                                             NEXT_STATION_SOUND + EXTENSION),
                                                         'event_type': 'AFTERSTATION', 'sorting': 1,
                                                         'pause': 0}})

            first_station_audio_template.append({'substitution': {'id_template': pre_finite_station_template_id,
                                                                  'substitution_code': 'NEXT_STOP',
                                                                  'substitution_file_type': 'FEMALE_SOUND',
                                                                  'sorting': 2,
                                                                  'pause': 0, 'event_type': 'AFTERSTATION'}})

            finite_station_audio_template.append({'resources': {'id_entity': pre_finite_station_template_id,
                                                                'id_audio_file': self.get_audio_id_by_file_name(
                                                                    FINITE_SOUND + EXTENSION),
                                                                'event_type': 'AFTERSTATION', 'sorting': 3,
                                                                'pause': 0}})

            # Аудиошаблон на промежуточные остановки
            station_audio_template.append({'resources': {'id_entity': station_template_id,
                                                         'id_audio_file': self.get_audio_id_by_file_name(
                                                             DJINGL_SOUND + EXTENSION),
                                                         'event_type': 'BEFORESTATION', 'sorting': 1,
                                                         'pause': 0}})

            station_audio_template.append({'substitution': {'id_template': station_template_id,
                                                            'substitution_code': 'THIS_STOP',
                                                            'substitution_file_type': 'FEMALE_SOUND',
                                                            'sorting': 2,
                                                            'pause': 0, 'event_type': 'BEFORESTATION'}})

            station_audio_template.append({'resources': {'id_entity': station_template_id,
                                                         'id_audio_file': self.get_audio_id_by_file_name(
                                                             NEXT_STATION_SOUND + EXTENSION),
                                                         'event_type': 'AFTERSTATION', 'sorting': 1,
                                                         'pause': 0}})

            station_audio_template.append({'substitution': {'id_template': station_template_id,
                                                            'substitution_code': 'NEXT_STOP',
                                                            'substitution_file_type': 'FEMALE_SOUND',
                                                            'sorting': 2,
                                                            'pause': 0, 'event_type': 'AFTERSTATION'}})

        self.append_audio_template_to_table(first_station_audio_template)
        self.append_audio_template_to_table(pre_finite_station_audio_template)
        self.append_audio_template_to_table(finite_station_audio_template)
        self.append_audio_template_to_table(station_audio_template)

    def append_audio_template_to_table(self, audio_templates):
        with self.conn.cursor() as curs:
            for template in audio_templates:
                main_key = next(iter(template))

                if main_key == 'resources':
                    curs.execute(querys.INSERT_INTO_TBL_TEMPLATE_AUDIO_RESOURCES, (template[main_key]['id_entity'],
                                                                                   template[main_key]['id_audio_file'],
                                                                                   template[main_key]['event_type'],
                                                                                   template[main_key]['sorting'],
                                                                                   template[main_key]['pause']))
                elif main_key == 'substitution':
                    curs.execute(querys.INSERT_INTO_TBL_TEMPLATE_AUDIO_SUBST, (template[main_key]['id_template'],
                                                                               template[main_key]['substitution_code'],
                                                                               template[main_key][
                                                                                   'substitution_file_type'],
                                                                               template[main_key]['sorting'],
                                                                               template[main_key]['pause'],
                                                                               template[main_key]['event_type']))

        print('Succesfully added audio tepmlate resources and substitutions')

    def get_audio_id_by_file_name(self, file_name: str):
        file_name_arr = file_name.split(" ")
        separator = "_"
        name = separator.join(file_name_arr)

        with self.conn.cursor() as curs:
            curs.execute(querys.GET_AUDIO_ID_BY_FILE_NAME, (name,))

            try:
                audio_id = curs.fetchall()[0][0]
            except IndexError as err:
                print('Index error when try find audio id by file name: ', err)
                audio_id = -1

        return audio_id

    def get_template_id_by_name(self, query: str, template_name: str):
        result = -1

        with self.conn.cursor() as curs:
            curs.execute(query, (template_name,))

            try:
                result = curs.fetchall()[0][0]
                print('Find audiotemplate for {}, with id {}'.format(template_name, result))
            except IndexError as err:
                print('Cand find audiotemplate for {}'.format(template_name), err)

        return result

    def connect_audio_template_to_stations(self):
        print('========================================')
        print('========================================')
        print('========================================')
        print('START_CONNECT_AUDIO_TEMPLATE_TO_STATIONS')
        print('========================================')
        print('========================================')
        print('========================================')

        # Забираем id аудиошаблонов
        start_station_template_id = self.get_template_id_by_name(querys.GET_TEMPLATE_ID_BY_NAME, 'Начальная')
        finite_station_template_id = self.get_template_id_by_name(querys.GET_TEMPLATE_ID_BY_NAME, 'Конечная')
        pre_finite_station_template_id = self.get_template_id_by_name(querys.GET_TEMPLATE_ID_BY_NAME, 'Предпоследняя')
        simple_station_template_id = self.get_template_id_by_name(querys.GET_TEMPLATE_ID_BY_NAME, 'Остановка')

        # Формируем содержимое шаблонов, причем коды раскрываем сразу
        start_station_template = self.collect_full_audio_template(start_station_template_id)
        print('Collect start station_template: ', start_station_template)
        simple_station_template = self.collect_full_audio_template(simple_station_template_id)
        print('Collect simple station_template: ', simple_station_template)
        pre_finite_station = self.collect_full_audio_template(pre_finite_station_template_id)
        print('Collect prefinite station_template: ', pre_finite_station)
        finite_station = self.collect_full_audio_template(finite_station_template_id)
        print('Collect finite station_template: ', finite_station)

        # Подготовили список остановок по маршруту
        prepared_route_desc = self.prepare_trips_per_route()

        # Теперь пробигаемся по тому, что получили. И навешиваем шаблоны на остановки
        # Если остановка первая и не имеет stop_mod = 6 - шаблон "Начальная"
        # Если остановка последння и не имеет stop_mod = 6 - шаблон "Конечная"
        # На все остальные кроме предпорследней - "Остановка
        for trip_info in prepared_route_desc:
            obj = prepared_route_desc[trip_info]

            # Одновременно добавляем в две таблицы
            # В tbl_tripstation_template - id из trips_stops и template_id
            # В tbl_trip_audio_resources - раскрываем шаблон, который навесили на остановку
            for count, stop_id in enumerate(obj['stops_id']):
                # Нашли начальную остановку
                print('=========================================')
                print('============BEFORE_ENTER_IN_FUNK=========')
                print('count: ', count)
                print('trip_id:', trip_info)
                print('stops_id', obj['stops_id'])
                print('stops_mods: ', obj['stops_mod'])
                print('trips_stop_id:', obj['id'])
                print('current stop_id: ', obj['stops_id'][count])
                print('current stop_mod: ', obj['stops_mod'][count])
                print('current trips_stop id:', obj['id'][count])
                print('=========================================')

                if obj['stops_mod'][count] == 2:
                    with self.conn.cursor() as curs:
                        curs.execute(querys.INSERT_INTO_TRIPSTATION_TEMPLATE, (obj['id'][count],
                                                                               start_station_template_id))

                    self.insert_into_trip_station_audio_resources(obj['route_id'],
                                                                  start_station_template, obj['stops_id'][count],
                                                                  obj['id'][count], obj['stops_id'][count + 1],
                                                                  obj['stops_id'][len(obj['stops_id']) - 1])
                # Нашли последнюю остановку
                if obj['stops_mod'][count] == 3:
                    with self.conn.cursor() as curs:
                        curs.execute(querys.INSERT_INTO_TRIPSTATION_TEMPLATE, (obj['id'][count],
                                                                               finite_station_template_id))

                    self.insert_into_trip_station_audio_resources(obj['route_id'],
                                                                  finite_station, obj['stops_id'][count],
                                                                  obj['id'][count])

                # Нашли предпоследнюю остановку
                elif obj['stops_mod'][count] == 1 and count == len(obj['stops_mod']) - 2:
                    with self.conn.cursor() as curs:
                        curs.execute(querys.INSERT_INTO_TRIPSTATION_TEMPLATE, (obj['id'][count],
                                                                               pre_finite_station_template_id))

                    self.insert_into_trip_station_audio_resources(obj['route_id'],
                                                                  pre_finite_station, obj['stops_id'][count],
                                                                  obj['id'][count], obj['stops_id'][count + 1],
                                                                  last_stop_id=obj['stops_id'][
                                                                      len(obj['stops_id']) - 1])
                # Нашли обысную остановку
                elif obj['stops_mod'][count] == 1 and count < len(obj['stops_mod']) - 2:
                    with self.conn.cursor() as curs:
                        curs.execute(querys.INSERT_INTO_TRIPSTATION_TEMPLATE, (obj['id'][count],
                                                                               simple_station_template_id))

                    self.insert_into_trip_station_audio_resources(obj['route_id'],
                                                                  simple_station_template, obj['stops_id'][count],
                                                                  obj['id'][count], obj['stops_id'][count + 1],
                                                                  obj['stops_id'][len(obj['stops_id']) - 1])

    def insert_into_trip_station_audio_resources(self, route_id, template, stop_id, trip_stop_id, next_stop_id=None,
                                                 last_stop_id=None):

        print('current stop_id: ', stop_id)
        print('trip_stop_id:', trip_stop_id)
        print('next_stop_id:', next_stop_id)

        with self.conn.cursor() as curs:
            for info in template:
                key = list(info)[0]

                audio_id = -1

                if key == 'resources':
                    curs.execute(querys.INSERT_INTO_TRIP_AUDIO_RESOURCES, (trip_stop_id, info[key][0], info[key][1],
                                                                           info[key][2], info[key][3]))
                    print('INSERT AUDIO RES:', curs.query)
                elif key == 'substitution':
                    code = info[key][0]
                    sorting = info[key][1]
                    pause = info[key][2]
                    event_type = info[key][3]

                    if code == THIS_STOP:
                        curs.execute(querys.GET_STATION_AUDIO_BY_STOP_ID, (stop_id,))
                        print('THIS_STOP:', curs.query)
                        try:
                            audio_id = curs.fetchall()[0][0]
                        except IndexError as err:
                            print('Cant find audio for stop with id:{}'.format(stop_id))
                        finally:
                            try:
                                curs.execute(querys.INSERT_INTO_TRIP_AUDIO_RESOURCES, (trip_stop_id, audio_id,
                                                                                       event_type, sorting, pause))
                                print(curs.query)
                            except psycopg2.errors.ForeignKeyViolation as err:
                                print("Error: ", err)

                    elif code == NEXT_STOP:
                        curs.execute(querys.GET_STATION_AUDIO_BY_STOP_ID, (next_stop_id,))
                        print('NEXT_STOP:', curs.query)
                        try:
                            audio_id = curs.fetchall()[0][0]
                        except IndexError as err:
                            print('Cant find audio for stop with id:{}'.format(next_stop_id))
                        finally:
                            try:
                                curs.execute(querys.INSERT_INTO_TRIP_AUDIO_RESOURCES, (trip_stop_id, audio_id,
                                                                                       event_type, sorting, pause))
                                print(curs.query)
                            except psycopg2.errors.ForeignKeyViolation as err:
                                print("Error: ", err)
                    elif code == END_STOP:
                        curs.execute(querys.GET_STATION_AUDIO_BY_STOP_ID, (last_stop_id,))
                        print('END_STOP:', curs.query)
                        try:
                            audio_id = curs.fetchall()[0][0]
                        except IndexError as err:
                            print('Cant find audio for stop with id:{}'.format(last_stop_id))
                        finally:
                            try:
                                curs.execute(querys.INSERT_INTO_TRIP_AUDIO_RESOURCES, (trip_stop_id, audio_id,
                                                                                       event_type, sorting, pause))
                                print(curs.query)
                            except psycopg2.errors.ForeignKeyViolation as err:
                                print("Error: ", err)
                    elif code == ROUTE_NUM:
                        curs.execute(querys.GET_ROUTE_AUDIO_BY_ROUTE_ID, (route_id[0],))
                        print('ROUTE_NUM:', curs.query)
                        try:
                            audio_id = curs.fetchall()[0][0]
                        except IndexError as err:
                            print('Cant find audio for route with id:{}'.format(route_id[0]))
                        finally:
                            try:
                                curs.execute(querys.INSERT_INTO_TRIP_AUDIO_RESOURCES, (trip_stop_id, audio_id,
                                                                                       event_type, sorting, pause))
                                print(curs.query)
                            except psycopg2.errors.ForeignKeyViolation as err:
                                print("Error: ", err)

    def collect_full_audio_template(self, template_id: int):
        audio_info = []

        with self.conn.cursor() as curs:
            curs.execute(querys.GET_AUDIO_RESOURCES_FROM_TEMPLATE, (template_id,))

            for resource in curs.fetchall():
                audio_info.append({'resources': resource})

            curs.execute(querys.GET_AUDIO_SUBSTITUTION_FROM_TEMPLATE, (template_id,))
            for substitution in curs.fetchall():
                audio_info.append({'substitution': substitution})

        return audio_info

    # TODO: Это штука тоже должна вызываться один разок
    def insert_text_template(self):
        print('========================================')
        print('========================================')
        print('========================================')
        print('======START_CREATE_TEXT_TEMPLATE========')
        print('========================================')
        print('========================================')
        print('========================================')

        first_station_template = additionalFunc.create_template('Начальная', 'Текстовый шаблон для начальной станции')
        pre_finite_station_template = additionalFunc.create_template('Предпоследняя',
                                                                     'Текстовый шаблон на предпоследнюю остановку')
        finite_station_template = additionalFunc.create_template('Конечная', 'Текстовый шаблон на конечную остановку')
        simple_station_template = additionalFunc.create_template('Обычная', 'Текстовый шаблон на обычную остановку')

        with self.conn.cursor() as curs:
            curs.execute(querys.INSERT_TEXT_TBL_TEMPLATE,
                         (first_station_template['name'], first_station_template['description']))
            first_station_template_id = curs.fetchall()[0][0]

            curs.execute(querys.INSERT_TEXT_TBL_TEMPLATE,
                         (pre_finite_station_template['name'], pre_finite_station_template['description']))
            pre_finite_station_template_id = curs.fetchall()[0][0]

            curs.execute(querys.INSERT_TEXT_TBL_TEMPLATE,
                         (finite_station_template['name'], finite_station_template['description']))
            finite_station_template_id = curs.fetchall()[0][0]

            curs.execute(querys.INSERT_TEXT_TBL_TEMPLATE,
                         (simple_station_template['name'], simple_station_template['description']))
            simple_station_template_id = curs.fetchall()[0][0]

        text_templates_info = []

        # Формируем список текста на шаблон
        with self.conn.cursor() as curs:
            # Делаем фейковую вставку в tbl_text_values, чтобы получить реальный id
            curs.execute(querys.INSERT_INTO_TBL_TEXT_VALUES, ('test', 1, 0))
            self.text_value_id = curs.fetchall()[0][0]

            # NOTE: Каждый шаблон - плюс единица к max_template_id
            # Каждая запись - плюс единица max_text_id

            # Начальная
            self.create_text_template(first_station_template_id, text_templates_info, [ONSTATION, AFTERSTATION],
                                      ["{" + THIS_STOP_TEXT + LED_INTERNAL + "}",
                                       "Следующая: " + TEXT_SEPARATOR + "{" + NEXT_STOP_TEXT + LED_INTERNAL + "}"],
                                      [1, 1], [0, 0])

            # Конечная
            self.create_text_template(finite_station_template_id, text_templates_info, [BEFORESTATION, ONSTATION],
                                      ["{" + THIS_STOP_TEXT + LED_INTERNAL + "}",
                                       "Конечная"],
                                      [1, 1], [0, 0])

            # Предпоследняя
            self.create_text_template(pre_finite_station_template_id, text_templates_info,
                                      [BEFORESTATION, AFTERSTATION],
                                      ["{" + THIS_STOP_TEXT + LED_INTERNAL + "}",
                                       "Следующая: " + TEXT_SEPARATOR + "{" + NEXT_STOP_TEXT + LED_INTERNAL + "}" + TEXT_SEPARATOR + " Конечная"],
                                      [1, 1], [0, 0])

            # Обычная
            self.create_text_template(simple_station_template_id, text_templates_info, [BEFORESTATION, AFTERSTATION],
                                      ["{" + THIS_STOP_TEXT + LED_INTERNAL + "}",
                                       "Следующая: " + TEXT_SEPARATOR + "{" + NEXT_STOP_TEXT + LED_INTERNAL + "}"],
                                      [1, 1], [0, 0])

            print('Collected templates: ', len(text_templates_info))

            for template in text_templates_info:
                curs.execute(querys.INSERT_INTO_TBL_TEXT_VALUES, (template['led_internal_line_1_text'],
                                                                  template['type'], template['exposure']))
                curs.execute(querys.INSERT_INTO_TBL_TEXT_TEMPLATE_RES, (template['id_template'],
                                                                        template['event_type'],
                                                                        template['led_internal_line_1_id']))

            print('Successfully added text templates')

    def create_text_template(self, template_id, source_list, events_type, led_internal_line_1_texts, types, exposures):
        for count, event in enumerate(events_type):
            self.text_value_id += 1
            source_list.append({'id_template': template_id, 'event_type': events_type[count],
                                'led_internal_line_1_id': self.text_value_id,
                                'led_internal_line_1_text': led_internal_line_1_texts[count],
                                'type': types[count], 'exposure': exposures[count]})

    def get_stations_with_text(self):
        result = None

        with self.conn.cursor() as curs:
            curs.execute(querys.GET_STOPS_WITH_TEXT_FROM_DEST, (DEPOT_ID,))
            result = curs.fetchall()

        return result

    def connect_text_to_stations(self, src_stops_with_text: list):
        with self.conn.cursor() as curs:
            curs.execute(querys.CLEAR_STATION_TEXT_RESOURCES, (DEPOT_ID,))

        print('Got {} station with text resources from src'.format(len(src_stops_with_text)))

        dest_stops_with_text_info = self.get_stations_with_text()

        dest_stops_id = []
        for info in dest_stops_with_text_info:
            dest_stops_id.append(info[0])

        # Формируем список остановок, у которых нет привязанных текстовых ресурсов
        stops_without_text = []
        for stop_with_text in src_stops_with_text:
            if stop_with_text[0] not in dest_stops_id:
                stops_without_text.append(stop_with_text)

        print('Find {} stops without text resources'.format(len(stops_without_text)))

        if len(stops_without_text) != 0:
            stop_id_key = 0
            event_type_key = 1
            internal_text_key = 2

            with self.conn.cursor() as curs:
                for stop in stops_without_text:
                    curs.execute(querys.INSERT_INTO_TBL_TEXT_VALUES, (stop[internal_text_key], 1, 0))
                    text_value_id = curs.fetchall()[0][0]
                    curs.execute(querys.INSERT_INTO_TBL_STATION_TEXT_RESOURCES, (stop[stop_id_key],
                                                                                 stop[event_type_key],
                                                                                 text_value_id,
                                                                                 text_value_id,
                                                                                 text_value_id))

    def connect_text_template_to_tripstation(self):
        print('========================================')
        print('========================================')
        print('========================================')
        print('START_CONNECT_TEXT_TEMPLATE_TO_STATIONS')
        print('========================================')
        print('========================================')
        print('========================================')

        with self.conn.cursor() as curs:
            curs.execute(querys.CLEAR_TRIPSTATION_TEXT_TEMPLATE, (DEPOT_ID,))

        # Забираем id текстовых шаблонов
        start_station_template_id = self.get_template_id_by_name(querys.GET_TEXT_TEMPLATE_ID_BY_NAME, 'Начальная')
        finite_station_template_id = self.get_template_id_by_name(querys.GET_TEXT_TEMPLATE_ID_BY_NAME, 'Конечная')
        pre_finite_station_template_id = self.get_template_id_by_name(querys.GET_TEXT_TEMPLATE_ID_BY_NAME,
                                                                      'Предпоследняя')
        simple_station_template_id = self.get_template_id_by_name(querys.GET_TEXT_TEMPLATE_ID_BY_NAME, 'Обычная')

        # Собираем полную информацию по маршруту
        start_station_template_info = self.collect_full_text_template_info(start_station_template_id)
        finite_station_template_info = self.collect_full_text_template_info(finite_station_template_id)
        pre_finite_station_template_info = self.collect_full_text_template_info(pre_finite_station_template_id)
        simple_station_template_info = self.collect_full_text_template_info(simple_station_template_id)

        prepared_route_desc = self.prepare_trips_per_route()

        # Ну а теперь все разбираем и начинаем накидывать текстовые шаблоны
        for trip_info in prepared_route_desc:
            obj = prepared_route_desc[trip_info]

            for count, stop_id in enumerate(obj['stops_id']):
                # Нашли начальную остановку
                if obj['stops_mod'][count] == 2:
                    with self.conn.cursor() as curs:
                        try:
                            curs.execute(querys.INSERT_INTO_TBL_TEXT_TRIPSTATION_TEMPLATE,
                                         (obj['id'][count], start_station_template_id))
                        except psycopg2.errors.UniqueViolation as err:
                            print('Error: ', err)

                    self.insert_into_tbl_trip_station_text_resources(obj['id'][count], start_station_template_info)

                # Нашли последнюю остановку
                if obj['stops_mod'][count] == 3:
                    with self.conn.cursor() as curs:
                        try:
                            curs.execute(querys.INSERT_INTO_TBL_TEXT_TRIPSTATION_TEMPLATE, (obj['id'][count],
                                                                                            finite_station_template_id))
                        except psycopg2.errors.UniqueViolation as err:
                            print('Error: ', err)

                    self.insert_into_tbl_trip_station_text_resources(obj['id'][count], finite_station_template_info)

                # Нашли предпоследнюю остановку
                elif obj['stops_mod'][count] == 1 and count == len(obj['stops_mod']) - 2:
                    with self.conn.cursor() as curs:
                        try:
                            curs.execute(querys.INSERT_INTO_TBL_TEXT_TRIPSTATION_TEMPLATE, (obj['id'][count],
                                                                                            pre_finite_station_template_id))
                        except psycopg2.errors.UniqueViolation as err:
                            print('Error: ', err)

                    self.insert_into_tbl_trip_station_text_resources(obj['id'][count], pre_finite_station_template_info)
                # Нашли обысную остановку
                elif obj['stops_mod'][count] == 1 and count < len(obj['stops_mod']) - 2:
                    with self.conn.cursor() as curs:
                        try:
                            curs.execute(querys.INSERT_INTO_TBL_TEXT_TRIPSTATION_TEMPLATE, (obj['id'][count],
                                                                                            simple_station_template_id))
                        except psycopg2.errors.UniqueViolation as err:
                            print('Error: ', err)

                    self.insert_into_tbl_trip_station_text_resources(obj['id'][count], simple_station_template_info)

    def collect_full_text_template_info(self, template_id: int):
        result = []
        id_template_key = 2
        event_type_key = 3
        internal_line1 = 5
        internal_line2 = 6

        with self.conn.cursor() as curs:
            curs.execute(querys.GET_TEXT_TEMPLATE_RESOURCES_BY_ID, (template_id,))
            raw_result = curs.fetchall()

            for info in raw_result:
                result.append({'id_template': info[id_template_key], 'event_type': info[event_type_key],
                               'led_internal_line_1': info[internal_line1],
                               'led_internal_line_2': info[internal_line2]})

        return result

    def insert_into_tbl_trip_station_text_resources(self, trip_stop_id, template_info: list):
        with self.conn.cursor() as curs:
            for template in template_info:
                try:
                    curs.execute(querys.INSERT_INTO_TBL_TRIP_STATION_TEXT_RESOURCES, (trip_stop_id,
                                                                                      template['event_type'],
                                                                                      template['led_internal_line_1'],
                                                                                      template['led_internal_line_2']))
                except psycopg2.errors.UniqueViolation as err:
                    print('Error: ', err)

    def prepare_trips_per_route(self):
        # Вытаскиваем остановки по маршрутам
        with self.conn.cursor() as curs:
            curs.execute(querys.GET_STOPS_PER_TRIPS, (DEPOT_ID,))
            trip_stops_query_result = curs.fetchall()

        # Оформленный список остановок по маршруту. Здесь к конкретному маршруту будут собраны все остановки
        route_description = {}
        trip_id = -1

        for trip_stop in trip_stops_query_result:
            if trip_id != trip_stop[4]:
                trip_id = trip_stop[4]
                route_description['trip_{}'.format(trip_stop[4])] = {'id': [trip_stop[0], ],
                                                                     'stops_id': [trip_stop[1], ],
                                                                     'stops_seq': [trip_stop[2], ],
                                                                     'stops_mod': [trip_stop[3], ],
                                                                     'route_id': [trip_stop[5], ]}
            else:
                route_description['trip_{}'.format(trip_stop[4])]['id'].append(trip_stop[0])
                route_description['trip_{}'.format(trip_stop[4])]['stops_id'].append(trip_stop[1])
                route_description['trip_{}'.format(trip_stop[4])]['stops_seq'].append(trip_stop[2])
                route_description['trip_{}'.format(trip_stop[4])]['stops_mod'].append(trip_stop[3])

        print('Prepared route description: ', len(route_description))
        return additionalFunc.prepare_route_description(route_description)

    def connect_text_to_routes(self, src_routes_with_text: list):
        dest_routes_with_text_info = self.get_routes_with_text()

        dest_routes_id = []
        for info in dest_routes_with_text_info:
            dest_routes_id.append(info[0])

        routes_without_text = []
        for route_with_text in src_routes_with_text:
            if route_with_text[0] not in dest_routes_id:
                routes_without_text.append(route_with_text)

        print('Find {} routes without text resources'.format(len(routes_without_text)))

        if len(routes_without_text) != 0:
            route_id_key = 0
            event_type_key = 1
            front_line_1_key = 2
            front_line_2_key = 3
            num_line_1_key = 4
            num_line_2_key = 5

            with self.conn.cursor() as curs:
                curs.execute(querys.GET_MAX_TEXT_VALUE_ID)
                text_value_id = curs.fetchall()[0][0]

                for route in routes_without_text:
                    text_value_id += 1
                    curs.execute(querys.INSERT_INTO_TBL_TEXT_VALUES, (route[front_line_1_key], 1, 0))
                    curs.execute(querys.INSERT_INTO_TBL_TEXT_VALUES, (route[front_line_2_key], 1, 0))
                    curs.execute(querys.INSERT_INTO_TBL_TEXT_VALUES, (route[num_line_1_key], 0, 0))
                    curs.execute(querys.INSERT_INTO_TBL_TEXT_VALUES, (route[num_line_2_key], 0, 0))
                    curs.execute(querys.INSERT_INTO_ROUTE_TEXT_RESOURCES, (route[route_id_key], route[event_type_key],
                                                                           text_value_id + 1, text_value_id + 2,
                                                                           text_value_id + 3, text_value_id + 4))

    def get_routes_with_text(self):
        with self.conn.cursor() as curs:
            curs.execute(querys.GET_ROUTE_WITH_TEXT_FROM_DEST)
            result = curs.fetchall()

        return result

    # Метод, который добавляет вспомогательные звуки для аудиошаблонов, такие как джингл, следует, конечная и тп
    def add_additional_sounds(self):
        audio_to_add = [
            {querys.NAME: DJINGL_SOUND, querys.SOURCE_NAME: DJINGL_SOUND + EXTENSION},
            {querys.NAME: MGT_SOUND, querys.SOURCE_NAME: MGT_SOUND + EXTENSION},
            {querys.NAME: SLED_DO_SOUND, querys.SOURCE_NAME: SLED_DO_SOUND + EXTENSION},
            {querys.NAME: TO_STATION_SOUND, querys.SOURCE_NAME: TO_STATION_SOUND + EXTENSION},
            {querys.NAME: NEXT_STATION_SOUND, querys.SOURCE_NAME: NEXT_STATION_SOUND + EXTENSION},
            {querys.NAME: GOOD_TRIP_SOUND, querys.SOURCE_NAME: GOOD_TRIP_SOUND + EXTENSION},
            {querys.NAME: FINITE_SOUND, querys.SOURCE_NAME: FINITE_SOUND + EXTENSION},
            {querys.NAME: GOODBY_SOUND, querys.SOURCE_NAME: GOODBY_SOUND + EXTENSION}
        ]

        tbl_file_audio_info = additionalFunc.prepare_audio_to_write(audio_to_add)
        self.add_audio_to_tbl_file(tbl_file_audio_info)

    def connect_text_to_trips(self):
        with self.conn.cursor() as curs:
            curs.execute(querys.CLEAR_TRIP_TEXT_RESOURCES, (DEPOT_ID,))
            curs.execute(querys.GET_TEXT_FOR_TRIP_WITHOUT_RESOURCES, (DEPOT_ID,))
            trip_without_text_resources_info = curs.fetchall()

        trip_id_key = 0
        stop_mods_key = 1
        stop_seqs_key = 2
        stop_names_key = 3
        nums_key = 4

        trips_panel_info = []
        # Из полученного списка оставим только информацию о последних остановках
        for trip_stations_info in trip_without_text_resources_info:
            stops_count = len(trip_stations_info[stop_mods_key])

            # Надо определить, что там с последней остановкой, надо ее выкинуть или нет
            if trip_stations_info[stop_mods_key][stops_count - 1] == 6 and \
                    trip_stations_info[stop_mods_key][stops_count - 2] == 3:
                trips_panel_info.append({'trip_id': trip_stations_info[trip_id_key],
                                         'panel_info': trip_stations_info[stop_names_key][stops_count - 2],
                                         'num': trip_stations_info[nums_key][0]})
            elif trip_stations_info[stop_mods_key][stops_count - 1] == 6 or trip_stations_info[stop_mods_key][stops_count - 1] == 3:
                trips_panel_info.append({'trip_id': trip_stations_info[trip_id_key],
                                         'panel_info': trip_stations_info[stop_names_key][stops_count - 1],
                                         'num': trip_stations_info[nums_key][0]})
            else:
                trips_panel_info.append({'trip_id': trip_stations_info[trip_id_key],
                                         'panel_info': trip_stations_info[stop_names_key][stops_count - 1],
                                         'num': trip_stations_info[nums_key][0]})

        print('Collect {} routes to insert into tbl_trip_text_resources'.format(len(trips_panel_info)))

        with self.conn.cursor() as curs:
            for info in trips_panel_info:
                curs.execute(querys.INSERT_INTO_TBL_TEXT_VALUES, (info['panel_info'], 0, 0))
                text_id = curs.fetchall()[0][0]

                curs.execute(querys.INSERT_INTO_TBL_TEXT_VALUES, (info['num'], 0, 0))
                num_id = curs.fetchall()[0][0]

                print('trip_id: {}, side_panel: {}, front_panel: {}, route_num: {}'
                      .format(info['trip_id'], info['panel_info'], info['panel_info'], info['num']))

                curs.execute(querys.INSERT_INTO_TBL_TRIP_TEXT_RESOURCES, (info['trip_id'], 'NOEVENT',
                                                                          text_id, None,  # led_side
                                                                          text_id, None,  # led_front
                                                                          num_id, None,))  # led_num
