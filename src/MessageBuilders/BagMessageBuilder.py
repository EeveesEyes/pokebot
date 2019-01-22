import logging
import time
from io import BytesIO

import telegram
from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup

import Constants
import DBAccessor
import Message
import Pokemon


def build_msg_bag(bot, chat_id, page_number: int):
    pokecount = 8
    player = DBAccessor.get_player(chat_id)
    if player is None:
        bot.send_message(chat_id=chat_id,
                         text='I have not met you yet. Want to be a Pok\xe9mon trainer? Type /catch.')
        return

    pokemon_sprite_list = []
    caption = ''
    if len(player.pokemon) > pokecount:
        caption = '*Page Number: *' + str(page_number) + '  Pok\xe9 ' + str(
            page_number * pokecount) + '-' + str((page_number + 1) * pokecount) + '/' + str(len(player.pokemon)) + '\n'
    list_start = pokecount * page_number
    list_end = pokecount * (page_number + 1) if len(player.pokemon) >= pokecount * (page_number + 1) else len(
        player.pokemon)
    page_list = player.pokemon[list_start:list_end]
    keys = []
    for pokemon in page_list:
        # sprites = [v[1] for v in i.sprites.items() if v[1] is not None]
        # caption += '#' + str(pokemon.pokedex_id) + ' ' + str(pokemon.name) + ' ' + str(int(pokemon.level)) + '\n'
        # pokemon_sprite_list.append(sprites[random.randint(0, len(sprites) - 1)])
        keys.append([InlineKeyboardButton(text=pokemon.name,
                                          callback_data='pokemon-display-' + str(pokemon._id))])
        pokemon_sprite_list.append(pokemon.sprites['front'])
    image = Pokemon.build_pokemon_bag_image(pokemon_sprite_list)

    for i in player.get_messages(Constants.BAG_MSG):
        try:
            bot.delete_message(chat_id=player.chat_id, message_id=i._id)
        except telegram.error.BadRequest as e:
            logging.error(e)
    if image is not None:
        bio = BytesIO()
        bio.name = 'image_bag_' + str(chat_id) + '.png'
        image.save(bio, 'PNG')
        bio.seek(0)

        keys.append([])
        if page_number > 0:
            keys[-1].append(InlineKeyboardButton(text='\u2190',
                                                 callback_data='bag-page-' + str(page_number - 1)))
        if len(player.pokemon) > list_end:
            keys[-1].append(InlineKeyboardButton(text='\u2192',
                                                 callback_data='bag-page-' + str(page_number + 1)))

        reply_markup = InlineKeyboardMarkup(inline_keyboard=keys)

        msg = bot.send_photo(chat_id=chat_id,
                             photo=bio,
                             reply_markup=reply_markup,
                             caption=caption, parse_mode=ParseMode.MARKDOWN)
    else:
        msg = bot.send_message(chat_id=chat_id,
                               text='Your bag is empty, catch some pokemon!')
    player.messages_to_delete.append(
        Message.Message(_id=msg.message_id, _title=Constants.BAG_MSG, _time_sent=time.time()))
    update = DBAccessor.get_update_query(messages_to_delete=player.messages_to_delete)
    DBAccessor.update_player(_id=player.chat_id, update=update)
