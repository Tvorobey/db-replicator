import databaseConnection


def main():
    # Init DB connection
    mgt_source_base = databaseConnection.source_db()
    mgt_source_base.connect()
    mgt_dest_base = databaseConnection.dist_db()
    mgt_dest_base.connect()

    # Добавление всяких технических звуков
    #mgt_dest_base.add_additional_sounds()

    # Добавление аудио на остановки и маршруты
    mgt_dest_base.connect_audio_to_station(mgt_source_base.get_sound_source_per_station())

    mgt_dest_base.connect_audio_to_route(mgt_source_base.get_sound_per_route())

    # Создание и применение аудиошаблонов
    #mgt_dest_base.create_audio_template()  # +
    mgt_dest_base.connect_audio_template_to_stations()  # +

    # TODO: перед новыми добавлениями сделать удаление всего, что оносится к данному роуту

    # Создание и применение текстовых шаблонов на остановки
    #mgt_dest_base.insert_text_template()
    # Навешиваем название остановки на саму остановку
    mgt_dest_base.connect_text_to_stations(mgt_source_base.get_stops_with_text_resources())
    # а вот тут уже раскрываем шаблоны на остановки трипа
    mgt_dest_base.connect_text_template_to_tripstation()

    mgt_dest_base.connect_text_to_routes(mgt_source_base.get_routes_with_text_resources())
    mgt_dest_base.connect_text_to_trips()


if __name__ == '__main__':
    main()
