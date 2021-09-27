# Запрос, который возвращает информацию по остановкам и звукам из боевой базы
# Также представлены наименования колонок
NAME = 0
SOURCE_NAME = 1
SOUND_ID = 2
STOP_ID = 3
STOP_NAME = 4

#TODO: Где стоит топорно depot_id там нужно сделать прокидывание через параметр

# Из этого запроса нас интересует name - это представление нормального текста, в текст, который лежит в папке dst
SOUND_PER_STATION = "with columns as (SELECT trips_stops.route_id, route_short_name, trip_id, trip_short_name," \
                    " direction_id, stop_sequence, stop_mode, trips_stops.stop_id, stop_name, stop_lon, stop_lat " \
                    "FROM trips_stops INNER JOIN route_by_depot ON trips_stops.route_id = route_by_depot.route_id " \
                    "INNER JOIN stop ON trips_stops.stop_id = stop.stop_id WHERE depot_id = %s " \
                    "ORDER BY route_short_name, trip_short_name, direction_id, stop_sequence), sound_on_stop as " \
                    "(select sound_id, stop_sounds.stop_id, stop_name from columns left join stop_sounds " \
                    "on columns.stop_id = stop_sounds.stop_id) select distinct name, source_name, sound_id," \
                    " stop_id,stop_name from sounds join sound_on_stop on sound_on_stop.sound_id = sounds.id and description_id = 22;"

# Вытаскиваем аудио, у которых есть гарантированно два привязанных звука (MALE и FEMALE). Такие станции мы считаем за
# четко привязанные
GET_STOP_AUDIO_FROM_DIST = "with routes as (select route_id from transport.route_by_depot where depot_id = 120), " \
                           "stops_sound as (select distinct ts.stop_id, tsa.file_id from transport.trips_stops ts " \
                           "inner join routes on routes.route_id = ts.route_id " \
                           "inner join resources.tbl_station_audio tsa on tsa.stop_id = ts.stop_id " \
                           "order by ts.stop_id), grouped as (select stops_sound.stop_id, count(stops_sound.stop_id) " \
                           "as count from stops_sound group by stops_sound.stop_id) select grouped.stop_id from grouped " \
                           "where count > 1;"

# OLD QUERY
#"SELECT stop_id from resources.tbl_station_audio;"


ADD_AUDIO_TO_DEST = "INSERT INTO resources.tbl_file (active, createdby, updatedat, updatedby, name, description," \
                    "comments, version, file_name, size, file_content_type, location, file_type, crc, duration," \
                    "category, tag) " \
                    "VALUES (true, null, null, null, null, %s, null, null, %s, 35249, %s, null, 'FEMALE_SOUND'," \
                    "%s, 1, null, null) returning id;"

GET_AUDIO_ID_BY_DESCRIPTION = "SELECT max(id) FROM resources.tbl_file WHERE description = (%s);"

INSERT_INTO_TBL_STATION_AUDIO = "INSERT INTO resources.tbl_station_audio (stop_id, file_id) VALUES(%s, %s);"

#Забираем из боевой базы маршруты с привязанными звуками
GET_SOUND_ON_ROUTE_FROM_SOURCE = "with columns as (SELECT trips_stops.route_id, route_short_name, trip_id, " \
                                 "trip_short_name, direction_id, stop_sequence, stop_mode, trips_stops.stop_id, " \
                                 "stop_name, stop_lon, stop_lat FROM trips_stops INNER JOIN route_by_depot " \
                                 "ON trips_stops.route_id = route_by_depot.route_id " \
                                 "INNER JOIN stop ON trips_stops.stop_id = stop.stop_id " \
                                 "WHERE depot_id = %s ORDER BY route_short_name, trip_short_name, direction_id, " \
                                 "stop_sequence), sound_on_route as (select sound_id, route_sounds.route_id, " \
                                 "route_short_name from columns left join route_sounds " \
                                 "on columns.route_id = route_sounds.route_id) select distinct name, source_name, " \
                                 "sound_id, route_id, route_short_name from sounds join sound_on_route " \
                                 "on sound_on_route.sound_id = sounds.id and description_id = 22;"

#Забираем из тестовой базы маршруты, у которых гарантированно есть два привязанных звука
GET_ROUTE_WITH_AUDIO_FROM_DEST  = "with routes as (select route_id from transport.route_by_depot where depot_id = %s)," \
                          " audio_per_route as (select routes.route_id, resources.tbl_route_audio.file_id from routes " \
                          "left join resources.tbl_route_audio on routes.route_id = resources.tbl_route_audio.route_id) " \
                          "select distinct route_short_name, trips_stops.route_id from transport.trips_stops " \
                          "join audio_per_route on audio_per_route.route_id = trips_stops.route_id and audio_per_route.file_id notnull;"

INSERT_INTO_TBL_ROUTE_AUDIO = "INSERT INTO resources.tbl_route_audio (route_id, file_id) VALUES (%s, %s);"

GET_AUDIO_ID_BY_FILE_NAME = "SELECT MAX(id) FROM resources.tbl_file WHERE file_name = %s;"

GET_MAX_AUDIO_TEMPLATE_ID = "SELECT MAX(id) FROM resources.tbl_template;"

GET_MAX_TEXT_TEMPLATE_ID = "SELECT max(id) FROM resources.tbl_text_template;"

GET_MAX_TEXT_VALUE_ID = "SELECT max(id) FROM resources.tbl_text_template_resources;"

INSERT_INTO_TBL_TEMPLATE_AUDIO_RESOURCES = "insert into resources.tbl_template_audio_resources " \
                                           "(id_entity, id_audio_file, event_type, sorting, pause, valid_date)" \
                                           "values (%s, %s, %s, %s, %s, null)"

INSERT_INTO_TBL_TEMPLATE_AUDIO_SUBST = "insert into resources.tbl_template_audio_substitutions" \
                                       " (id_template, substitution_code, substitution_file_type, sorting, pause," \
                                       " valid_date, event_type, full_code) " \
                                       "values (%s, %s, %s, %s, %s, null, %s, null);"

INSERT_AUDIO_TBL_TEMPLATE = "insert into resources.tbl_template (name, description, comments, category, dt_start, dt_end)" \
                            "VALUES (%s, %s, null, null, null, null) returning id;"

INSERT_TEXT_TBL_TEMPLATE = "insert into resources.tbl_text_template (name, description, comments, category, dt_start, dt_end)" \
                      "VALUES (%s, %s, null, null, null, null) returning id;"

GET_TEMPLATE_ID_BY_NAME = "select max(id) from resources.tbl_template where name = %s;"

GET_STOPS_PER_TRIPS = "SELECT  ts.id, stop_id, stop_sequence, stop_mode, trip_id, rd.route_id FROM transport.trips_stops ts " \
                      "INNER JOIN transport.route_by_depot rd ON ts.route_id = rd.route_id " \
                      "INNER JOIN transport.depot d ON d.depot_id = rd.depot_id " \
                      "WHERE d.depot_id = %s ORDER BY trip_id, stop_sequence"

INSERT_INTO_TRIPSTATION_TEMPLATE = "INSERT INTO resources.tbl_tripstation_template (id_tripstation, id_template)" \
                                   "VALUES (%s, %s);"

INSERT_INTO_TRIP_AUDIO_RESOURCES = "INSERT INTO resources.tbl_trip_station_audio_resources " \
                                   "(id_entity, id_audio_file, event_type, sorting, pause, valid_date)" \
                                   " VALUES (%s, %s, %s, %s, %s, null);"

GET_AUDIO_RESOURCES_FROM_TEMPLATE = "SELECT id_audio_file, event_type, sorting, pause " \
                                    "FROM resources.tbl_template_audio_resources WHERE id_entity = %s;"

GET_AUDIO_SUBSTITUTION_FROM_TEMPLATE = "SELECT substitution_code, sorting, pause, event_type " \
                                       "FROM resources.tbl_template_audio_substitutions where id_template = %s;"

GET_STATION_AUDIO_BY_STOP_ID = "SELECT file_id FROM resources.tbl_station_audio tsa inner join resources.tbl_file tf " \
                               "on tf.id = tsa.file_id and tsa.stop_id = %s and tf.file_type = 'FEMALE_SOUND';"

GET_ROUTE_AUDIO_BY_ROUTE_ID = "SELECT file_id FROM resources.tbl_route_audio WHERE route_id = %s;"

INSERT_INTO_TBL_TEXT_VALUES = "INSERT INTO resources.tbl_text_values (values, type, exposure, separator)" \
                              "VALUES (%s, %s, %s, null) returning id;"

INSERT_INTO_TBL_TEXT_TEMPLATE_RES = "insert into resources.tbl_text_template_resources " \
                                    "(id_template, id_text_file, event_type, valid_date, led_internal_line_1," \
                                    " led_internal_line_2, lcd_text_line_1, lcd_text_line_2, led_side_line_1," \
                                    " led_side_line_2, led_front_line_1, led_front_line_2)" \
                                    " VALUES (%s, null, %s, null, %s, null, null, null, null, null, null, null);"

GET_STOPS_WITH_TEXT_FROM_SOURCE = "with routes as (select route_id from route_by_depot where depot_id = %s) " \
                                  "select distinct stop_id, event_type, tv.values as internal_text, " \
                                  "tv1.values as lcd_text, tv2.values as side_text from trips_stops " \
                                  "inner join routes on routes.route_id = trips_stops.route_id " \
                                  "inner join resources.tbl_station_text_resources on stop_id = id_entity " \
                                  "left join resources.tbl_text_values tv on led_internal_line_1 = tv.id " \
                                  "left join resources.tbl_text_values tv1 on lcd_text_line_1 = tv1.id " \
                                  "left join resources.tbl_text_values tv2 on led_side_line_1 = tv2.id;"

# TODO: Дополнить запрос, так как он выдает лишь полный перечень id остановок, не опираясь на то
# есть ли у них текстовые ресурсы
GET_STOPS_WITH_TEXT_FROM_DEST = "with routes as (select route_id from transport.route_by_depot where depot_id = %s)" \
                                "select stop_id from transport.trips_stops ts " \
                                "inner join routes on routes.route_id = ts.route_id " \
                                "inner join resources.tbl_station_text_resources on id_entity = stop_id;"

                                # OLD QUERY GET_STOPS_WITH_TEXT_FROM_DEST
                                #"with routes as (select route_id from transport.route_by_depot where depot_id = %s)" \
                                #"select stop_id from transport.trips_stops " \
                                #"inner join routes on routes.route_id = trips_stops.route_id;"

INSERT_INTO_TBL_STATION_TEXT_RESOURCES = "insert into resources.tbl_station_text_resources " \
                                         "(id_entity, id_text_file, event_type, valid_date, led_internal_line_1," \
                                         " led_internal_line_2, lcd_text_line_1, lcd_text_line_2, led_side_line_1," \
                                         " led_side_line_2) values (%s, null, %s, null, %s, null, %s, null, %s, null);"

GET_TEXT_TEMPLATE_ID_BY_NAME = "select max(id) from resources.tbl_text_template where name = %s;"

GET_TEXT_TEMPLATE_RESOURCES_BY_ID = "select * from resources.tbl_text_template_resources where id_template = %s;"

INSERT_INTO_TBL_TEXT_TRIPSTATION_TEMPLATE = "insert into resources.tbl_tripstation_text_template (id_tripstation, id_template) " \
                                       "VALUES (%s, %s);"

INSERT_INTO_TBL_TRIP_STATION_TEXT_RESOURCES = "insert into resources.tbl_trip_station_text_resources " \
                                              "(id_entity, id_text_file, event_type, valid_date, led_internal_line_1," \
                                              " led_internal_line_2, lcd_text_line_1, lcd_text_line_2, led_side_line_1," \
                                              " led_side_line_2, led_front_line_1, led_front_line_2) " \
                                              "values (%s, null, %s, null, %s, %s, null, null, null, null, null, null);"

GET_ROUTE_WITH_TEXT_FROM_SOURCE = "with routes as (select route_id from route_by_depot where depot_id = %s) " \
                                  "select distinct trips_stops.route_id, event_type, tv.values as front_line_1, " \
                                  "tv1.values as front_line_2, tv2.values as num_line_1, " \
                                  "tv3.values as num_line_2 from trips_stops " \
                                  "inner join routes on routes.route_id = trips_stops.route_id " \
                                  "inner join resources.tbl_route_text_resources on routes.route_id = id_entity " \
                                  "left join resources.tbl_text_values tv on led_front_line_1 = tv.id " \
                                  "left join resources.tbl_text_values tv1 on led_front_line_2 = tv1.id " \
                                  "left join resources.tbl_text_values tv2 on led_num_line_1 = tv2.id " \
                                  "left join resources.tbl_text_values tv3 on led_num_line_2 = tv3.id;"

GET_ROUTE_WITH_TEXT_FROM_DEST = "select distinct id_entity from resources.tbl_route_text_resources;"

INSERT_INTO_ROUTE_TEXT_RESOURCES = "insert into resources.tbl_route_text_resources " \
                                   "(id_entity, id_text_file, event_type, valid_date, led_front_line_1," \
                                   " led_front_line_2, led_num_line_1, led_num_line_2) " \
                                   "values (%s, null, %s, null, %s, %s, %s, %s);"

GET_TRIP_WITH_TEXT_RESOURCES_FROM_SRC = "with routes as (select route_id from route_by_depot where depot_id = 120) " \
                                        "select trip_id, event_type, tv.values as internal_line_1, " \
                                        "tv2.values as internal_line_2, tv3.values as side_line_1, " \
                                        "tv4.values as side_line_2, tv5.values as front_line_1, " \
                                        "tv6.values as front_line_2, tv7.values as num_line_1, " \
                                        "tv8.values as num_line_2 " \
                                        "from public.trip inner join routes on routes.route_id = trip.route_id " \
                                        "inner join resources.tbl_trip_text_resources " \
                                        "on trip.trip_id = tbl_trip_text_resources.id_entity " \
                                        "left join resources.tbl_text_values tv on led_internal_line_1 = tv.id " \
                                        "left join resources.tbl_text_values tv2 on led_internal_line_2 = tv2.id " \
                                        "left join resources.tbl_text_values tv3 on led_side_line_1 = tv3.id " \
                                        "left join resources.tbl_text_values tv4 on led_side_line_2 = tv4.id " \
                                        "left join resources.tbl_text_values tv5 on led_front_line_1 = tv5.id " \
                                        "left join resources.tbl_text_values tv6 on led_front_line_2 = tv6.id " \
                                        "left join resources.tbl_text_values tv7 on led_num_line_1 = tv7.id " \
                                        "left join resources.tbl_text_values tv8 on led_num_line_2 = tv8.id;"

GET_TRIP_WITH_TEXT_RESOURCES_FROM_DEST = "with routes as " \
                                         "(select route_id from transport.route_by_depot where depot_id = %s) " \
                                         "select trip_id from transport.trip " \
                                         "inner join routes on routes.route_id = transport.trip.route_id " \
                                         "inner join resources.tbl_trip_text_resources " \
                                         "on trip.trip_id = tbl_trip_text_resources.id_entity;"

INSERT_INTO_TBL_TRIP_TEXT_RESOURCES = "insert into resources.tbl_trip_text_resources " \
                                      "(id_entity, id_text_file, event_type, valid_date, led_internal_line_1," \
                                      " led_internal_line_2, led_side_line_1, led_side_line_2, led_front_line_1," \
                                      " led_front_line_2, led_num_line_1, led_num_line_2) " \
                                      "values (%s, null, %s, null, null, null, %s, %s, %s, %s, %s, %s);"

GET_MAX_AUDIO_FILE_ID = "select max(id) from resources.tbl_file;"

GET_TEXT_FOR_TRIP_WITHOUT_RESOURCES = "with routes as (select route_id from transport.route_by_depot " \
                                      "where depot_id = %s), trips as (select trip_id from transport.trips_stops ts " \
                                      "inner join routes on ts.route_id = routes.route_id), " \
                                      "trips_and_text as (select trips.trip_id, ttts.id_entity from trips " \
                                      "left join resources.tbl_trip_text_resources ttts on trip_id = ttts.id_entity), " \
                                      "trips_without_text as (select trip_id, tat.id_entity from trips_and_text tat " \
                                      "where tat.id_entity isnull) select trip_id, array_agg(mode) as mods, " \
                                      "array_agg(seq) as seqs, array_agg(name) as names, array_agg(route_num) as num " \
                                      "from (select distinct ts.trip_id as trip_id, ts.stop_mode as mode, " \
                                      "ts.stop_sequence as seq, s.stop_name as name, " \
                                      "ts.route_short_name as route_num from transport.trips_stops ts " \
                                      "inner join trips_without_text on ts.trip_id = trips_without_text.trip_id " \
                                      "inner join transport.stop s on ts.stop_id = s.stop_id order by trip_id, seq) " \
                                      "sorted_table group by trip_id;"

CLEAR_STATION_TEXT_RESOURCES = "delete from resources.tbl_station_text_resources tstr where tstr.id_entity in " \
                               "(select stop_id from transport.trips_stops ts where ts.route_id in " \
                               "(select rbd.route_id from transport.route_by_depot rbd where rbd.depot_id = %s))"

CLEAR_TRIPSTATION_TEXT_TEMPLATE = "delete from resources.tbl_tripstation_text_template tttt where tttt.id_tripstation in " \
                                  "(select id from transport.trips_stops ts where ts.route_id in " \
                                  "(select rbd.route_id from transport.route_by_depot rbd where rbd.depot_id = %s))"

CLEAR_TRIP_TEXT_RESOURCES = "delete from resources.tbl_trip_text_resources tttr where tttr.id_entity in " \
                            "(select id from transport.trips_stops ts where ts.route_id in " \
                            "(select rbd.route_id from transport.route_by_depot rbd where rbd.depot_id = %s))"