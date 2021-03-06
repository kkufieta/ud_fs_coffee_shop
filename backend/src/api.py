import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
Uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
# db_drop_and_create_all()


# ======
# ROUTES
# ======
'''
GET /drinks
    it should be a public endpoint
    it should contain only the drink.short() data representation
returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
    or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['GET'])
def get_drinks():
    drinks = Drink.query.all()
    drinks = [drink.short() for drink in drinks]
    return jsonify({
        'success': True,
        'drinks': drinks
    })


'''
GET /drinks-detail
    it should require the 'get:drinks-detail' permission
    it should contain the drink.long() data representation
returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
    or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(jwt_payload):
    drinks = Drink.query.all()
    drinks = [drink.long() for drink in drinks]
    return jsonify({
        'success': True,
        'drinks': drinks
    })


'''
POST /drinks
    it should create a new row in the drinks table
    it should require the 'post:drinks' permission
    it should contain the drink.long() data representation
returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
    or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def post_drink(jwt_payload):
    body = request.get_json()
    if not body:
        abort(400)
    if not all(key in body for key in ['title', 'recipe']):
        abort(422)
    title = body['title']
    recipe = body['recipe']
    if not isinstance(recipe, list):
        abort(422)
    for recipe_part in recipe:
        if not all(key in recipe_part for key in ['color', 'name', 'parts']):
            abort(422)
    recipe = json.dumps(recipe)
    try:
        drink = Drink(title=title, recipe=recipe)
        drink.insert()
        return jsonify({
            'success': True,
            'drinks': drink.long()
        })
    except Exception:
        abort(400)


'''
PATCH /drinks/<id>
    where <id> is the existing model id
    it should respond with a 404 error if <id> is not found
    it should update the corresponding row for <id>
    it should require the 'patch:drinks' permission
    it should contain the drink.long() data representation
returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
    or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drink(jwt_payload, id):
    if not id:
        abort(404)
    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        if not drink:
            abort(404)
        body = request.get_json()
        if not body:
            abort(400)
        if not any(key in body for key in ['title', 'recipe']):
            abort(400)
        if 'title' in body:
            drink.title = body['title']
        if 'recipe' in body:
            recipe = body['recipe']
            if not isinstance(recipe, list):
                abort(422)
            for recipe_part in recipe:
                if not all(
                    key in recipe_part for key in [
                        'color',
                        'name',
                        'parts']):
                    abort(422)
            drink.recipe = json.dumps(body['recipe'])
        drink.update()
        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        })
    except Exception:
        abort(404)


'''
DELETE /drinks/<id>
    where <id> is the existing model id
    it should respond with a 404 error if <id> is not found
    it should delete the corresponding row for <id>
    it should require the 'delete:drinks' permission
returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
    or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt_payload, id):
    if not id:
        abort(404)
    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        if not drink:
            abort(404)
        drink.update()
        drink.delete()
        return jsonify({
            'success': True,
            'delete': id
        })
    except Exception:
        abort(404)

# Error Handling


'''
Error handler for AuthError.
'''
@app.errorhandler(AuthError)
def auth_error(error):
    message, status_code = error.args

    return jsonify({
        'success': False,
        'error': status_code,
        'message': message['code'] + ': ' + message['description']
    }), status_code


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 400,
        'message': 'bad request'
    }), 400


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 401,
        'message': 'unauthorized'
    }), 401


@app.errorhandler(403)
def forbidden(error):
    return jsonify({
        'success': False,
        'error': 403,
        'message': 'forbidden'
    }), 403


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 404,
        'message': 'method not allowed'
    }), 404


@app.errorhandler(405)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 405,
        'message': 'method not allowed'
    }), 405


@app.errorhandler(422)
def unprocessable_entity(error):
    return jsonify({
        'success': False,
        'error': 422,
        'message': 'unprocessable entity'
    }), 422


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        'success': False,
        'error': 500,
        'message': 'internal server error'
    }), 500


@app.errorhandler(503)
def service_unavailable(error):
    return jsonify({
        'success': False,
        'error': 503,
        'message': 'service unavailable'
    }), 503
