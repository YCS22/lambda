var AWS = require("aws-sdk");
const cognito = new AWS.CognitoIdentityServiceProvider({
  apiVersion: "2016-04-18",
});

function updateUserAttribute(name, surname, username) {
  return new Promise((resolve, reject) => {
    let params = {
      UserAttributes: [
        {
          Name: "name",
          Value: `${name}`,
        },
        {
          Name: "family_name",
          Value: `${surname}`,
        },
      ],
      UserPoolId: "",
      Username: username,
    };
    cognito.adminUpdateUserAttributes(params, (err, data) =>
      err ? reject(err) : resolve(data)
    );
  });
}

exports.handler = async (event) => {
  const { surname, name, username } = JSON.parse(event.body).event.data.new;
  await updateUserAttribute(name, surname, username);

  const response = {
    statusCode: 200,
    
  };
  return response;
};