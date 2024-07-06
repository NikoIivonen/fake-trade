from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user
from .models import Note
from . import db

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    btc_price = 57000
    if request.method == 'POST':
        note = request.form.get('note')
        selected = request.form.get('options')
        print(note, selected)
        if len(note) < 1:
            flash('The amount cannot be empty.', category='error')
        else:
            if selected == 'Buy':
                if current_user.cash < float(note)*btc_price:
                    flash('Insufficient funds.', category='error')
                else:
                    current_user.bitcoin = current_user.bitcoin + float(note)
                    current_user.cash = current_user.cash - float(note)*btc_price
                    db.session.commit()

            elif selected == 'Sell':
                if current_user.bitcoin < float(note):
                    flash('Not enough bitcoin.', category='error')
                else:
                    current_user.bitcoin = current_user.bitcoin - float(note)
                    current_user.cash = current_user.cash + float(note)*btc_price
                    db.session.commit()

    return render_template("home.html", user=current_user, btcValue=btc_price)