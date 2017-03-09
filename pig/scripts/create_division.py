from sqlalchemy import func
import sys

# Idea for the future: Make classes to put in 'specializations' rather than checking if it's a list etc.

class DivisionCreator:

    def __init__(self, database, Division, Parameter, NumberParam, EnumVariant):
        self.database = database
        self.Division = Division
        self.Parameter = Parameter
        self.NumberParam = NumberParam
        self.EnumVariant = EnumVariant
        # Parameters under construction
        self.parameters = {} # int -> Parameter
        # Specialization of each Parameter
        self.specs = {} # int -> NumberParam or [EnumVariant]

    def register_division(self, current_user, form):
        #print('Registering division...', file=sys.stderr)
        #print('Input: %s' % form, file=sys.stderr)
        division = self.Division(name = form["Division"], creator_id = current_user.id)

        # First pass: Find the type of each parameter
        for (key, value) in form.items():
            if key == "Division":
                pass

            elif key.startswith("Parameter"):
                param_nr = int(key[9])

                parameter = self.database.get_session() \
                    .query(self.Parameter) \
                    .filter(value.strip().lower() == func.lower(self.Parameter.description)) \
                    .first()

                if parameter is None:
                    # Create new Parameter only if it does not exist
                    parameter = self.Parameter(description=value.strip())
                    self.database.get_session().add(parameter)
                    self.parameters[param_nr] = parameter
                else:
                    # Parameter already exists - Don't create it, just add it to the Division
                    # Setting it to None here signifies for later that we should not add a specialization for it
                    self.parameters[param_nr] = None
                    pass
                division.parameters.append(parameter)

            elif key.startswith("Type"):
                param_nr = int(key[4])
                if value == "Number":
                    self.specs[param_nr] = self.NumberParam(min=None, max=None)
                elif value == "Enum":
                    if (param_nr in self.specs) and isinstance(self.specs[param_nr], self.NumberParam):
                        pass
                    else:
                        self.specs[param_nr] = []

        # Commit the new Parameters so that they get assigned primary keys
        self.database.get_session().commit()

        # Second pass: Find the configurations for each parameters
        for (key, value) in form.items():

            if key.startswith("Min") or key.startswith("Max"):
                param_nr = int(key[3])
            elif key.startswith("Option"):
                param_nr = int(key[6])

            if not self.parameters[param_nr] is None:
                if isinstance(self.specs[param_nr], self.NumberParam):
                    if key.startswith("Min"):
                        self.specs[param_nr].min = int(value)
                    elif key.startswith("Max"):
                        self.specs[param_nr].max = int(value)
                elif isinstance(self.specs[param_nr], list):
                    # self.specs[param_nr] is a list of EnumVariant
                    if key.startswith("Option"):
                        self.specs[param_nr].append(self.EnumVariant(name=value))

        # Third pass: For every parameter, add it and its specialization to the database
        for param_nr in self.specs.keys():
            param = self.parameters[param_nr]
            # `param is None` signifies that the parameter was already in the Database, and that we should not
            # make another specialization
            if not param is None:
                if isinstance(self.specs[param_nr], self.NumberParam):
                    spec = self.specs[param_nr]
                    spec.parameter = param
                    self.database.get_session().add(spec)
                elif isinstance(self.specs[param_nr], list):
                    for variant in self.specs[param_nr]:
                        variant.parameter = param
                        self.database.get_session().add(variant)

        self.database.get_session().add(division)
        self.database.get_session().commit()

    def make_parameter(self, desc):
        parameter = self.database.get_session() \
            .query(self.Parameter) \
            .filter(desc.strip().lower() == func.lower(self.Parameter.description)) \
            .first()
        if parameter is None:
            parameter = self.Parameter(description=desc.strip())
        return parameter;


# Example for reference


#  form[Division] = navn
#  form[Parameter1] = en
#  form[Type1] = Enum
#  form[Min1] = 
#  form[Max1] = 
#  form[Option1_1] = a
#  form[Option1_2] = b
#  form[Option1_3] = c
#  form[Parameter2] = nu
#  form[Type2] = Number
#  form[Min2] = 0
#  form[Max2] = 10