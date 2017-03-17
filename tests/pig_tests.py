import os, pig, unittest
from pig.views import get_divisions, pig_key
from pig.db.models import *
from pig.db.database import *
from pig.scripts.DivideGroupsToLeaders import DivideGroupsToLeaders
from flask import Flask
from random import randint


class PigTestCase(unittest.TestCase):

    def setUp(self):
        pig.app.config['TESTING'] = True
        self.app = pig.app.test_client()
        self.database = Database(Flask(__name__))
        self.divide_groups_to_leaders = DivideGroupsToLeaders(self.database,Division,user_division)


    def login(self,username,password):
        return self.app.post("/login", data=dict(Username=username,Password=password),follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    # A helper method to setup the connection to the postgresDB on heroku
    def setup_db(self, uri="postgres://wtsceqpjdsbhxw:34df69f4132d39ea5b95e52822d6dedc8e3eb368915cb8888526f896f21bce75@ec2-54-75-229-201.eu-west-1.compute.amazonaws.com:5432/dfa7tvu04d7t6i" ):
        temp = Database(Flask(__name__))
        temp.set_uri(uri)
        return temp

    #A helper method that sends a post request to the register page containing all of the registration-info
    def register(self, email, password, password_confirm, first_name, last_name):
        return self.app.post("/register", data=dict(Email=email, Password=password, PasswordConfirm=password_confirm, FirstName=first_name, LastName=last_name))

    def create_user(self, email, password, first_name, last_name):
        self.database.get_session().execute("INSERT INTO users (firstname,lastname,email,password) VALUES('" +first_name+"','" + last_name+"','" + email +"','"+password+"')")
        self.database.get_session().commit()


    def create_users_with_given_parameters_for_usertype_and_count(self,type,count):
        for i in range(count):
            self.database.get_session().execute("INSERT INTO users (firstname,lastname,email,password) VALUES('first"+type+str(i)+"','last"+type+str(i)+"','"+type+str(i)+"@email.com','password')")
        self.database.get_session().commit()


    def delete_user(self, email):
        self.database.get_session().execute("DELETE FROM users WHERE email = '" + email + "'")
        self.database.get_session().commit()


    def create_division(self, name, creator_id):
        division = Division(name=name, creator_id=creator_id)
        self.database.get_session().add(division)
        self.database.get_session().commit()

    def get_division(self,name,creator_id):
        return self.database.get_session()\
            .query(Division).filter(Division.creator_id == creator_id, Division.name == name).first()


    def delete_division(self, id):
        self.database.get_session().execute("DELETE FROM user_division WHERE division_id = " + str(id))
        self.database.get_session().execute("DELETE FROM division WHERE id = " + str(id))
        self.database.get_session().commit()


    def get_user(self, email):
        return self.database.get_session().query(User).filter(User.email == email).first()


    def get_users_where_id_is_larger_or_equal_to_parameter_and_in_interval(self,minVal,size):
        return self.database.get_session().query(User).filter(User.id>=minVal,User.id < minVal+size)


    def delete_users_where_id_is_larger_or_equal_to_parameter_and_in_interval(self,minVal,size):
        self.database.get_session().execute("DELETE FROM users WHERE id >= " + str(minVal) + " AND id <" + str(minVal+size))
        self.database.get_session().commit()

    def go_to_division(self, link):
        return self.app.get("/" + link)

    def create_single_group_with_given_division_id(self, division_id):
        group = Group(division_id= division_id)
        self.database.get_session().add(group)
        self.database.get_session().commit()

    def create_multiple_groups_with_given_division_id(self,division_id, count):
        for i in range(count):
            self.database.get_session().execute("INSERT INTO groups (division_id) VALUES('"+str(division_id)+"')")
        self.database.get_session().commit()


    def get_groups_using_only_division_id(self,division_id):
        return self.database.get_session().query(Group).filter(Group.division_id == division_id)

    def sign_up_users_for_division_as_leader(self,leaders,division_id):
        for leader in leaders:
            self.database.get_session().execute\
                ("INSERT INTO user_division (user_id, division_id,role) VALUES('"+str(leader.id)+ "','" + str(division_id)+"','Leader')")
        self.database.get_session().commit()

    def delete_all_groups_in_given_division(self,division_id):
        self.database.get_session().execute("DELETE FROM groups WHERE division_id ="+str(division_id))

    def delete_from_user_division_with_given_division_id(self,division_id,count):
        for i in range(count):
            self.database.get_session().execute("DELETE FROM user_division WHERE division_id=" + str(division_id))
        self.database.get_session().commit()

    def get_user_division_on_given_division_id(self,division_id):
        return self.database.get_session().query(user_division).filter(user_division._columns.get("division_id")==division_id).all()

    # Testing connection to db with invalid uri, this is done by setting up a new connection to the db, and then changing the uri,
    # see setup_db.
    def test_connect_to_db_with_invalid_uri(self):
        data = None
        database = self.setup_db(uri = "postgres://wtsceqpjdsbhxw")
        try:
            data = database.get_session().query(User).first()
        except Exception as e1:
            print(e1)
        finally:
            assert data is None

    def test_connect_to_db_with_valid_uri(self):
        data = None
        database = self.setup_db()
        try:
            data = database.get_session().query(User).first()
        except Exception as e:
            print(e)
        finally:
            assert data is not None

    # Testing login with an invalid username
    def test_login_invalid_username(self):
        self.create_user('valid@email.com','password','firstname','firstname')
        rv = self.login('invalid','password')

        self.delete_user('valid@email.com')
        assert b'firstname' not in rv.data

    # Testing login with a valid username, but invalid password
    def test_login_invalid_password(self):
        self.create_user('valid@email.com','password','firstname','lastname')
        rv = self.login('valid@email.com','wrong password')

        self.delete_user('valid@email.com')
        assert b'firstname' not in rv.data

    # Testing login with valid username and password, and then logging out.
    def test_login_and_logout_valid_username_and_password(self):
        self.create_user('valid@email.com','password','firstname','lastname')
        rv = self.login('valid@email.com','password')

        assert b'firstname' in rv.data
        rv = self.logout()
        assert b'firstname' not in rv.data

        self.delete_user('valid@email.com')

    # TODO: Skriv ferdig denne!!
    def test_create_division(self):
        pass

    #A helper method that sends a post request to the register page containing all of the registration-info
    def register(self, email, password, password_confirm, first_name, last_name):
        return self.app.post("/register", data=dict(Email=email, Password=password, PasswordConfirm=password_confirm, FirstName=first_name, LastName=last_name))

    #The methods below are pretty self explainatory; they all query the database and they are used by the testing methods
    #instead of them directly querying the database.
    def delete_user(self, email):
        self.database.get_session().execute("DELETE FROM users WHERE email = '" + email + "'")
        self.database.get_session().commit()

    def create_division(self, name, creator_id):
        division = Division(name=name, creator_id=creator_id)
        self.database.get_session().add(division)
        self.database.get_session().commit()

    def delete_division(self, id):
        self.database.get_session().execute("DELETE FROM user_division WHERE division_id = " + str(id))
        self.database.get_session().execute("DELETE FROM division WHERE id = " + str(id))
        self.database.get_session().commit()

    def get_user(self, email):
        return self.database.get_session().query(User).filter(User.email == email).first()

    def go_to_division(self, link):
        return self.app.get("/" + link)

    #Testing registration of a user with two different passwords
    def test_register_user_with_two_different_password_inputs(self):
        rv = self.register("asd@asd.com", "test", "test1", "tester", "testing")
        assert b'does not match.' in rv.data

    #Testing registration of a user with invalid email by checking if the feedback contains a part of the string it displays to the user
    #when entering the wrong email.
    def test_register_user_with_invalid_email(self):
        rv = self.register("asd@asd", "test", "test", "tester", "testing")
        assert b'email was invalid.' in rv.data
        rv = self.register("asd@as@d", "test", "test", "tester", "testing")
        assert b'email was invalid.' in rv.data
        rv = self.register("as..d@asd", "test", "test", "tester", "testing")
        assert b'email was invalid.' in rv.data

    #Testing if it is possible to register a user with one ore more empty fields. It does this by following the redirect after posting the
    #registration form then checking if it received the exepcted output.
    def test_register_user_with_one_or_more_empty_fields(self):
        rv = self.register("asd@asd.com", "", "test", "tester", "testing")
        assert b'fields are filled.' in rv.data
        rv = self.register("asd@asd.com", "test", "", "tester", "testing")
        assert b'fields are filled.' in rv.data
        rv = self.register("", "test", "test", "tester", "testing")
        assert b'fields are filled.' in rv.data
        rv = self.register("asd@asd.com", "test", "test", "", "testing")
        assert b'fields are filled.' in rv.data
        rv = self.register("asd@asd.com", "test", "test", "tester", "")
        assert b'fields are filled.' in rv.data
        rv = self.register("", "", "", "", "")
        assert b'fields are filled.' in rv.data

    #Testing if its possible to register a user
    def test_register_user_with_valid_data(self):
        self.register("asd@asd.com", "test", "test", "test", "test")
        user = self.database.get_session().query(User).filter(User.email == "asd@asd.com").first()
        assert user is not None

    #Tests if it is able to remove a user from the database
    def test_remove_user_from_database(self):
        user = self.get_user("asd@asd.com")
        if user is None:
            return
        self.delete_user("asd@asd.com")
        user = self.get_user("asd@asd.com")
        assert user is None

    #Tests if it is able to register a certain user to a certain division through the site. It generates the link for the signup based on data from the page
    #Then follows the url and checks if it gets the desired output.
    def test_register_user_as_student_for_division(self):
        self.register("tester@asd.com", "test", "test", "Asd", "asdtest")
        self.register("tester1@asd.com", "test", "test", "Asd1", "asdtest")
        user = self.get_user("tester@asd.com")
        user1 = self.get_user("tester1@asd.com")
        self.create_division("testing_division", user.id)
        division = self.database.get_session().query(Division).filter(Division.creator_id == user.id, Division.name == "testing_division").first()
        self.login("tester1@asd.com", "test")
        link = get_divisions.get_link(pig_key, division.name, division.id, 1)
        rv = self.go_to_division(link)
        assert b'registered you as a' in rv.data
        self.delete_division(division.id)
        self.delete_user(user.email)
        self.delete_user(user1.email)

    def test_divide_groups_to_leaders_with_varying_range_of_leaders_and_groups(self):

        group_count = randint(15, 25)
        leader_count = randint(3, 7)

        self.create_user("creator@email.com","password",'firstCreator','lastCreator')
        self.create_users_with_given_parameters_for_usertype_and_count("leader",leader_count)

        creator = self.get_user('creator@email.com')
        first_leader = self.get_user('leader0@email.com')
        leaders = self.get_users_where_id_is_larger_or_equal_to_parameter_and_in_interval(first_leader.id,leader_count)

        self.create_division("test division",creator.id)
        division = self.get_division("test division", creator.id)

        self.create_multiple_groups_with_given_division_id(division_id=division.id,count=group_count)

        self.sign_up_users_for_division_as_leader(leaders=leaders,division_id=division.id)


        self.divide_groups_to_leaders.assign_leaders_to_groups(current_user=creator,division_id=division.id)

        groups = self.database.get_session().query(Group).filter(Group.division_id == division.id)

        for element in groups:
            assert (element.leader_id >= first_leader.id and element.leader_id < first_leader.id + leader_count)

        self.delete_all_groups_in_given_division(division.id)
        self.delete_from_user_division_with_given_division_id(division.id, leader_count)
        self.delete_division(division.id)
        self.delete_user('creator@email.com')
        self.delete_users_where_id_is_larger_or_equal_to_parameter_and_in_interval(first_leader.id,leader_count)


if __name__ == '__main__':
    unittest.main()
