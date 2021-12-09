const fetch = require("node-fetch");
const hasuraAdminSecret ="";
const url = "";

var getdeleteEnum = {
  isNull: 1,
  isFilled: 2,
};

async function delete_message(conversation_id) {
  const variables = {
    conversation_id: conversation_id,
  };
  const getdeletedat = ` 
  query MyQuery($conversation_id:uuid) {
            conversation_user(where: {conversation_id: {_eq: $conversation_id}}) {
            deleted_at
            }  
          }
          `;

  const deleted_date = await fetch(url, {
    method: "POST",
    body: JSON.stringify({
      query: getdeletedat,
      variables,
    }),
    headers: {
      "content-type": "application/json",
      "x-hasura-admin-secret": hasuraAdminSecret,
    },
  })
    .then((response) => response.json())
    .then(({ data }) => {
      return data.conversation_user;
    });

  let minDate;
  if (deleted_date[0].deleted_at < deleted_date[1].deleted_at) {
    minDate = deleted_date[0].deleted_at;
  } else {
    minDate = deleted_date[1].deleted_at;
  }

  const deletevariables = {
    conversation_id: conversation_id,
    date: minDate,
  };
 
  const deletemessage = ` 
mutation MyMutation($date: timestamptz, $conversation_id: uuid) {
  delete_conversation_messages(where: {created_at: {_lte: $date}, conversation_id: {_eq: $conversation_id}}) {
    affected_rows
  }
}

          `;

  await fetch(url, {
    method: "POST",
    body: JSON.stringify({
      query: deletemessage,
      variables:deletevariables,
    }),
    headers: {
      "content-type": "application/json",
      "x-hasura-admin-secret": hasuraAdminSecret,
    },
  })
    .then((response) => response.json())
    .then(({ data }) => {
      console.log("data",data)
      return data;
    });

  return false;
}

async function get_deleted_at(conversation_id) {
  const variables = {
    conversation_id: conversation_id,
  };
  const getdeletedat = ` 
  query MyQuery($conversation_id:uuid) {
            conversation_user(where: {conversation_id: {_eq: $conversation_id}}) {
            deleted_at
            }  
          }
          `;

  const deleted_date = await fetch(url, {
    method: "POST",
    body: JSON.stringify({
      query: getdeletedat,
      variables,
    }),
    headers: {
      "content-type": "application/json",
      "x-hasura-admin-secret": hasuraAdminSecret,
    },
  })
    .then((response) => response.json())
    .then(({ data }) => {
      return data.conversation_user;
    });

  let status;

  if (
    deleted_date[0].deleted_at != null &&
    deleted_date[1].deleted_at != null
  ) {
    status = getdeleteEnum.isFilled;
  } else {
    status = getdeleteEnum.isNull;
  }

  return status;
}

async function update_deleted_at(conversation_id, user_id) {
  const variables = {
    user_id: user_id,
    conversation_id: conversation_id,
  };
  const updatedeletedat = ` 
            mutation MyMutation($user_id: String!, $conversation_id: uuid!) {
            update_conversation_user(where: {conversation_id: {_eq: $conversation_id}, user_id:{_eq: $user_id}}, _set: {deleted_at: "now()"}) {
            affected_rows
            returning {
            deleted_at
            }}}`;

  const deleted_date = await fetch(url, {
    method: "POST",
    body: JSON.stringify({
      query: updatedeletedat,
      variables,
    }),
    headers: {
      "content-type": "application/json",
      "x-hasura-admin-secret": hasuraAdminSecret,
    },
  })
    .then((response) => response.json())
    .then(({ data }) => {
      return data.update_conversation_user.returning[0].deleted_at;
    });
  //return deleted_date;
  return deleted_date;
}

exports.handler = async (event) => {
  const data = JSON.parse(event.body);
  const { conversation_id, user_id } = data.input.arg1;

  const updateresult = await update_deleted_at(conversation_id, user_id);

  var status = await get_deleted_at(conversation_id).then(async (result) => {
    if (result == getdeleteEnum.isFilled) {
      await delete_message(conversation_id);
    }

    return {
      result: "OK",
    };
  });

  return {
    result: updateresult,
  };
};
