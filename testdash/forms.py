from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo, NumberRange


class SetupForm(FlaskForm):  # Validation form for setup
    login = StringField('login', validators=[DataRequired(), Length(4, 32)])
    name = StringField('name', validators=[Length(0, 48)])
    password = PasswordField('password', validators=[DataRequired(), Length(4, 128)])
    repeat_password = PasswordField('repeat_password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('complete')


class SignInForm(FlaskForm):  # Validation form for sign in
    login = StringField('login', validators=[DataRequired(), Length(4, 32)])
    password = PasswordField('password', validators=[DataRequired(), Length(4, 128)])
    remember = BooleanField('remember')
    submit = SubmitField('signin')


class NewUserForm(FlaskForm):  # Validation form for new user creation
    login = StringField('login', validators=[DataRequired(), Length(4, 32)])
    name = StringField('name', validators=[Length(0, 48)])
    password = PasswordField('password', validators=[DataRequired(), Length(4, 128)])
    repeat_password = PasswordField('repeat_password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('create')


class EditUserNameForm(FlaskForm):  # Validation form for user's name edit
    name = StringField('name', validators=[Length(0, 48)])
    submit_name = SubmitField('edit_name')


class EditUserPassForm(FlaskForm):  # Validation form for user's password edit
    password = PasswordField('password', validators=[DataRequired(), Length(4, 32)])
    repeat_password = PasswordField('repeat_password', validators=[DataRequired(), EqualTo('password')])
    submit_pass = SubmitField('edit_pass')


class DeleteUserForm(FlaskForm):  # Validation form for user delete
    login = StringField('login', validators=[DataRequired(), Length(4, 32)])
    submit = SubmitField('delete')


class ExecuteCommandForm(FlaskForm):  # Validation form for command execute
    command = StringField('command', validators=[DataRequired(), Length(1, 512)])
    directory = StringField('directory')
    timeout = IntegerField('timeout', validators=[DataRequired(), NumberRange(1, 8)])
    submit = SubmitField('execute')


class ConfirmForm(FlaskForm):  # Validation form for confirmations
    confirmation = PasswordField('login', validators=[DataRequired(), Length(4, 32)])
    submit = SubmitField('reset')
