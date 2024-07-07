from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user
from .models import User
from . import db
import requests

def get_btc_price():
    api_key = 'f3aec9ce-4146-4d49-86e0-01d9beca2f56'
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'

    parameters = {
        'symbol': 'BTC',
        'convert': 'USD'
    }

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': api_key,
    }

    response = requests.get(url, headers=headers, params=parameters)

    data = response.json()

    bitcoin_price = round(data['data']['BTC']['quote']['USD']['price'], 2)

    return bitcoin_price

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'], endpoint='home')
@login_required
def home():
    btc_price = get_btc_price()
    if request.method == 'POST':
        btc_price = get_btc_price()
        note = request.form.get('note')
        selected = request.form.get('options')

        if len(note) < 1:
            flash('The amount cannot be empty.', category='error')
        else:
            btc = float(note)
            if selected == 'Buy':
                if current_user.cash < btc*btc_price:
                    flash('Insufficient funds.', category='error')
                else:
                    current_user.bitcoin = current_user.bitcoin + btc
                    current_user.cash = current_user.cash - btc*btc_price
                    db.session.commit()

            elif selected == 'Sell':
                if current_user.bitcoin < btc:
                    flash('Not enough bitcoin.', category='error')
                else:
                    current_user.bitcoin = current_user.bitcoin - btc
                    current_user.cash = current_user.cash + btc*btc_price
                    db.session.commit()

    return render_template("home.html", user=current_user, btcValue=btc_price)

@views.route('/leaderboard', endpoint='leaderboard')
def leaderboard():
    users = User.query.all()
    btc_price = get_btc_price()
    return render_template("leaderboard.html", user=current_user, users=users, btc_price=btc_price)