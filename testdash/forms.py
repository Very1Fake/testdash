from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo


class SetupForm(FlaskForm):  # Temporary unused
    login = StringField('login', validators=[DataRequired(), Length(4, 64)])
    password = PasswordField('password', validators=[DataRequired(), Length(4, 128)])
    confirm_password = PasswordField('confirm_password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('complete')


class SignInForm(FlaskForm):  # Validation form for sign in
    login = StringField('login', validators=[DataRequired(), Length(4, 64)])
    password = PasswordField('password', validators=[DataRequired(), Length(4, 128)])
    remember = BooleanField('remember')
    submit = SubmitField('signin')
    # TODO: Remember me
