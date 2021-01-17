from wtforms import Form
from wtforms import StringField, BooleanField, IntegerField, DecimalField, DateField, SelectField

from wtforms.validators import DataRequired

class LoginForm(Form):
    openid = StringField('openid', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)

class BuyItemForm(Form):
    id = IntegerField('id', validators=[DataRequired()])
    name = SelectField('name', coerce=str, validators=[DataRequired()])
    articleNumber = StringField('articleNumber', validators=[DataRequired()])
    size = SelectField('size', coerce=str, validators=[DataRequired()])
    buyCost = DecimalField('buyCost', validators=[DataRequired()])
    soldTypeId = SelectField('soldTypeId', coerce=int, default=None)
    buyTypeId = SelectField('buyTypeId', coerce=int, validators=[DataRequired()])
    soldPrice = DecimalField('soldPrice', validators=[DataRequired()])
    soldPriceExpect = DecimalField('soldPriceExpect', validators=[DataRequired()])
    goodStatus = SelectField('goodStatus', validators=[DataRequired()])
    buyTime = DateField('buyTime', validators=[DataRequired()])
    soldTime = DateField('soldTime', validators=[DataRequired()])
    

