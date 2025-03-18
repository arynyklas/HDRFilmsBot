from src import dispatcher, bot, dispatcher_workflow


dispatcher.run_polling(  # type: ignore
    bot,
    **dispatcher_workflow
)
