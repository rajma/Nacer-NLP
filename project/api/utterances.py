import datetime
import spacy
import time
import json

from flask import Blueprint, jsonify, request, render_template

from project.api.models.intents import Intent 
from project.api.models.bots import Bot
from project import db, cache, interpreters, nlp, d, app
from sqlalchemy import exc

from project.config import DevelopmentConfig
from project.keys import super_secret

from project.shared.checkAuth import checkAuth

utterances_blueprint = Blueprint('utterances', __name__, template_folder='./templates')


@utterances_blueprint.route('/api/intents/<bot_guid>/<intent_name>/utterances', methods=['POST','PUT','DELETE'])
def intent(bot_guid,intent_name):
    try:
        code,user_id = checkAuth(request)
        # code = 200
        # user_id = 16
        if code == 200:
            global interpreters
            nlus = interpreters
            bot = Bot.query.filter_by(bot_guid=bot_guid).first()
            if bot:
                if bot.user_id == user_id:
                    intent = Intent.query.filter_by(bot_guid=bot_guid).filter_by(name=intent_name).first()
                    if intent:
                        model = bot.active_model
                        if model:
                            nlu = nlus[model]
                        else:
                            nlu = None
                        intent.modified = datetime.datetime.utcnow()
                        if request.method == 'POST':
                            post_data = request.get_json()
                            new_utterance = post_data['value']

                            stop_words = [" a "," an "," the "," is "]

                            utt_copy = new_utterance
                            for word in stop_words:
                                utt_copy = utt_copy.replace(word," ")
                            
                            utt_words = utt_copy.split(" ")

                            words_json = json.loads(bot.words) 
                            if type(words_json) == str:
                                words_json = {}
                            for word in utt_words:
                                if word in words_json:
                                    if intent_name in words_json[word]:
                                        words_json[word][intent_name] += 1
                                    else:
                                        words_json[word][intent_name] = 1
                                else:
                                    words_json[word] = {intent_name:1}

                            bot.words = json.dumps(words_json)
                            if new_utterance in intent.utterances:
                                app.logger.warning('POST /api/intents/'+ bot_guid +'/'+ intent_name +'/utterances utterance already exists')
                                return jsonify({})
                            else:
                                utts = [new_utterance] + intent.utterances
                                intent.utterances = [u for u in utts]
                                if nlu:
                                    int, entities, confidence = nlu.parse(new_utterance)
                                else:
                                    entities = []
                                try:
                                    db.session.commit()
                                except Exception as e:
                                    app.logger.error('POST /api/intents/'+ bot_guid +'/'+ intent_name +'/utterances ' + str(e))
                                    return jsonify({"success":False,"errors":str(e)})
                                app.logger.warning('POST /api/intents/'+ bot_guid +'/'+ intent_name +'/utterances utterance successfully added')
                                return jsonify({"utterance":new_utterance,"entities":entities})
                        elif request.method == 'PUT':
                            put_data = request.get_json()
                            old_utterance = put_data['old_utterance']
                            new_utterance = put_data['value']
                            intent.utterances = [new_utterance if u == old_utterance else u for u in intent.utterances]
                            intent.modified = datetime.datetime.utcnow()
                            int, entities, confidence = nlu.parse(new_utterance)
                            try:
                                db.session.commit()
                            except Exception as e:
                                app.logger.error('PUT /api/intents/'+ bot_guid +'/'+ intent_name +'/utterances ' + str(e))
                                return jsonify({"success":False,"errors":str(e)})
                            app.logger.info('PUT /api/intents/'+ bot_guid +'/'+ intent_name +'/utterances utterance successfully updated')
                            return jsonify({"utterance":new_utterance,"entities":entities})
                        elif request.method == 'DELETE':
                            old_utterance = request.args['utterance']
                            new_utterances = []
                            for utterance in intent.utterances:
                                if (utterance != old_utterance):
                                    new_utterances.append(utterance)
                            intent.utterances = new_utterances
                            intent.modified = datetime.datetime.utcnow()
                            try:
                                db.session.commit()
                            except Exception as e:
                                app.logger.error('DELETE /api/intents/'+ bot_guid +'/'+ intent_name +'/utterances ' + str(e))
                                return jsonify({"success":False,"errors":str(e)})
                            app.logger.info('DELETE /api/intents/'+ bot_guid +'/'+ intent_name +'/utterances utterance successfully deleted')
                            return jsonify({"success":True})
                    else:
                        app.logger.warning('/api/intents/'+ bot_guid +'/'+ intent_name +'/utterances intent does not exist')
                        return jsonify({"error":"Intent Doesn't exist"}),404 
        elif code == 400:
            app.logger.warning('/api/intents/'+ bot_guid +'/'+ intent_name +'/utterances invalid authorization token')
            return jsonify({"error":"Invalid Authorization Token"}),400
        elif code == 401:
            app.logger.warning('/api/intents/'+ bot_guid +'/'+ intent_name +'/utterances no authorization token sent')
            return jsonify({"error":"No Authorization Token Sent"}),401
    except Exception as e:
        app.logger.warning('/api/intents/'+ bot_guid +'/'+ intent_name +'/utterances ' + str(e))
        return jsonify({'success':False,'errors':str(e)}),400

