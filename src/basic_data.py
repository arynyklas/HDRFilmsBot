class TEXTS:
    class errors:
        class flood:
            message = "🚫 Не пишите слишком часто!"
            callback_query = "🚫 Не нажимайте слишком часто!"

        message = (
            "Произошла неизвестная ошибка!\n"
            "Напишите в поддержку\n"
            "\n"
            "Код ошибки: <code>{error_id}</code>"
        )

        callback_query = (
            "Произошла неизвестная ошибка!\n"
            "Напишите в поддержку\n"
            "\n"
            "Код ошибки: {error_id}"
        )

    start = (
        "👋 Привет!\n"
        "Чтобы посмотреть фильм/сериал просто пришли мне ссылку на него с помощью встроенной кнопки ниже:"
    )

    class inline_search:
        message_content = "<a href=\"{image_url}\">⁣</a>{title}\n{url}"
        result_description = "{entity_text} | {addition}"

    class data_updated:
        message = "Данные устарели"

        inline = (
            "К сожалению, старые данные теперь не рабочие\n"
            "Пожалуйста, нажмите на кнопку ниже чтобы снова выполнить поиск"
        )

    class short_info:
        default = (
            "Краткая информация:\n"
            "Название: <i>{title}</i>{original_title} {age}\n"
            "Рейтинги:\n"
            "{ratings}{slogan}{release_date}{country}{director}{genre}"
            "{track_series_text}"
        )

        attrs: dict[str, str] = dict(
            original_title = " (<i>{}</i>)",
            age            = "[<i>{}</i>]",
            slogan         = "\nСлоган: <i>{}</i>",
            release_date   = "\nДата выхода: <i>{}</i>",
            country        = "\nСтрана: <i>{}</i>",
            director       = "\nРежиссер: <i>{}</i>",
            genre          = "\nЖанр: <i>{}</i>"
        )

        rating_attr = "  - <i>{source}</i> - <i>{rating}</i>"

        class track_series:
            without_user = "\n\n<i>+ {users_count} человек отслеживают данный сериал</i>"
            with_user_more = "\n\n<i>+ <b>Вы</b> и ещё {users_count} человек отслеживают данный сериал</i>"
            with_user_alone = "\n\n<i>+ <b>Вы</b> отслеживаете данный сериал</i>"

    class enjoy:
        default = (
            "Выберите качество и наслаждайтесь!\n"
            "{series_text}"
            "\n"
            "Озвучка: <i>{translator}</i>"
        )

        series = "(сезон - {season_id}, серия - {episode_id})\n"

    class select:
        translator = "Выберите озвучку:"

        season = (
            "Выберите сезон:\n"
            "\n"
            "Озвучка: <i>{translator}</i>"
        )

        episode = (
            "Выберите серию:\n"
            "(сезон - {season_id})\n"
            "\n"
            "Озвучка: <i>{translator}</i>"
        )

        class download_quality_statuses:
            queue = "🔜 В очереди на загрузку..."

            downloading = "📤 Видео загружается в качестве {quality} ... {progress_percentage}%"
            uploading = "📤 Видео уже загружено и отправляется в качестве {quality} ..."

            class caption:
                default = (
                    "🎬 <i>{item_title}</i>\n"
                    "\n{series_text}"
                    "Озвучка: <i>{translator}</i>\n"
                    "В качестве <i>{quality}</i>"
                )

                series_test = "Сезон: {season_id}, серия: {episode_id}\n"

    class subscription:
        default = (
            "Подписка даёт возможность скачивать фильмы и сериалы в течении {days} дней\n"
            "Стоимость подписки: ⭐️ {price} звёзд"
        )

        class invoice:
            title = "Оплата подписки"
            description = "Подписка на скачивание фильмов и сериалов"
            price_label = "Подписка на {days} дней"

        paid = (
            "Подписка успешно оплачена!\n"
            "Теперь вы можете скачивать фильмы и сериалы в течении {days} дней!"
            "\n"
            "Спасибо за поддержку!"
        )

    class track_series:
        default = "✅ Сериал успешно добавлен в список отслеживания!"

        class updates:
            default = "🔔 Оповещения о сериале \"<i>{title}</i>\":\n{updates}"

            episode = "— 🆕 Серия {episode_digit} ({season_digit} сезон)"
            episodes = "— 🆕 Серия {episode_start_digit}-{episode_end_digit} ({season_digit} сезон)"
            season_episode = "— 🆕 Серия {episode_digit} (❇️ {season_digit} сезон)"
            season_episodes = "— 🆕 Серия {episode_start_digit}-{episode_end_digit} (❇️ {season_digit} сезон)"

    updated = "☑️ Ссылки обновлены!"

    class not_avaliable:
        default = "Фильм/сериал в настоящее время недоступен!"

        default_with_translator = (
            "Фильм/сериал в настоящее время недоступен!\n"
            "Озвучка: <i>{translator}</i>"
        )


class KB_TEXTS:
    inline = "🔍 Поиск"
    track_series = "👀 Отслеживать сериал"
    all_seasons = "📑 Список сезонов"
    update = "🔄 Обновить ссылки"
    subtitle = "🎬"
    external_player_url = "↗️ Перейти в плеер"
    send_as_video = "🌟 Отправить как видео"

    class subscription:
        generate_invoice = "💳 Оплатить подписку"
        back = "⬅️ Назад"

    return_to_translators = "⬅️ Озвучки"
    return_to_seasons = "⬅️ Сезоны"
