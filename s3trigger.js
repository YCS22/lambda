const { v4: uuidv4 } = require("uuid");
const AWS = require("aws-sdk");
const s3 = new AWS.S3();
const fetch = require("node-fetch");
const hasuraAdminSecret ="";
const url = "";

async function get_key(sub, name) {
  const variables = {
    entityId: sub,
    name: name,
  };
  const upsertUserQuery = ` 
  query MyQuery($name: String,$entityId:String) {
    media(where: {name: {_eq: $name}, entity_id: {_eq: $entityId}}) {path}}`;
  const path = await fetch(url, {
    method: "POST",
    body: JSON.stringify({
      query: upsertUserQuery,
      variables,
    }),
    headers: {
      "content-type": "application/json",
      "x-hasura-admin-secret": hasuraAdminSecret,
    },
  })
    .then((response) => response.json())
    .then(({ data }) => {
      return data.media[0].path;
    });
  return path;
}
async function get_entity_type_id(sub) {
  const variables = {
    sub: sub,
  };
  const upsertUserQuery = ` 
    query MyQuery($sub:uuid) {
    posts_aggregate(where: {id: {_eq: $sub}}) {
    aggregate {count}}}`;
  const count = await fetch(url, {
    method: "POST",
    body: JSON.stringify({
      query: upsertUserQuery,
      variables,
    }),
    headers: {
      "content-type": "application/json",
      "x-hasura-admin-secret": hasuraAdminSecret,
    },
  })
    .then((response) => response.json())
    .then(({ data }) => {
      return data.posts_aggregate.aggregate.count;
    });

  let response;
  if (count > 0) {
    const post = ` 
    query MyQuery {
    entity_types(where: {name: {_eq: "post"}}) {id}}`;
    response = await fetch(url, {
      method: "POST",
      body: JSON.stringify({
        query: post,
      }),
      headers: {
        "content-type": "application/json",
        "x-hasura-admin-secret": hasuraAdminSecret,
      },
    })
      .then((response) => response.json())
      .then(({ data }) => {
        return data.entity_types[0].id;
      });
  }
  if (count <= 0) {
    const user = ` 
    query MyQuery {
    entity_types(where: {name: {_eq: "user"}}) {id}}`;
    response = await fetch(url, {
      method: "POST",
      body: JSON.stringify({
        query: user,
      }),
      headers: {
        "content-type": "application/json",
        "x-hasura-admin-secret": hasuraAdminSecret,
      },
    })
      .then((response) => response.json())
      .then(({ data }) => {
        return data.entity_types[0].id;
      });
  }
  return response;
}
async function get_media_info(sub, name) {
  const variables = {
    sub: sub,
    name: name,
  };
  const upsertUserQuery = ` 
  query MyQuery($sub: String, $name: String) {
    media_aggregate(where: {entity_id: {_eq: $sub}, name: {_eq: $name}}) {
      aggregate {count}}}`;

  const count = await fetch(url, {
    method: "POST",
    body: JSON.stringify({
      query: upsertUserQuery,
      variables,
    }),
    headers: {
      "content-type": "application/json",
      "x-hasura-admin-secret": hasuraAdminSecret,
    },
  })
    .then((response) => response.json())
    .then(({ data }) => {
      return data.media_aggregate.aggregate.count;
    });
  return count;
}
async function post_media(sub, entity_type_id, key, name) {
  const get_media = await get_media_info(sub, name); // name bilgisini yollıycaz
  let response;

  if (get_media > 0) {
    const delete_key = await get_key(sub, name);
    const params = {
      Bucket: "webhasura",
      Key: `${delete_key}`,
    };

    await s3.deleteObject(params).promise();
    const variables = {
      entity_id: sub,
      path: key,
      name: name,
    };

    const upsertUserQuery = `
    mutation MyMutation($entity_id: String, $path: String,$name:String) {
      update_media(where: {entity_id: {_eq: $entity_id}, name: {_eq:$name}}, _set: {path: $path}) {
        affected_rows}}`;

    response = await fetch(url, {
      method: "POST",
      body: JSON.stringify({
        query: upsertUserQuery,
        variables,
      }),
      headers: {
        "content-type": "application/json",
        "x-hasura-admin-secret": hasuraAdminSecret,
      },
    })
      .then((response) => response.json())
      .then(({ data }) => {
        return data.update_media.affected_rows;
      });
  }

  if (get_media <= 0) {
    const variables = {
      entity_id: sub,
      entity_type_id: entity_type_id,
      path: key,
      name: name,
      id_uuid: sub
    };

    const upsertUserQuery = ` 
    mutation MyMutation($entity_type_id:uuid,$entity_id:String,$path:String,$name:String,$id_uuid:uuid) {
    insert_media(objects: {entity_type_id:$entity_type_id, entity_id: $entity_id, path:$path,name:$name,id_uuid:$id_uuid}) {
    affected_rows}}`;

    response = await fetch(url, {
      method: "POST",
      body: JSON.stringify({
        query: upsertUserQuery,
        variables,
      }),
      headers: {
        "content-type": "application/json",
        "x-hasura-admin-secret": hasuraAdminSecret,
      },
    })
      .then((response) => response.json())
      .then(({ data }) => {
        return data.insert_media.affected_rows;
      });
  }
  return response;
}
exports.handler = async (event) => {
  try {
    const data = JSON.parse(event.body);
    const { base64, sub, name } = data.input.arg1;
    let fileBuffer = Buffer.from(base64, "base64");
    const randomID = uuidv4();
    const params = {
      Bucket: "webhasura",
      Key: `${randomID}.png`,
      Body: fileBuffer,
      ContentEncoding: "base64",
    };
    let key = "";
    const { Key } = await s3.upload(params).promise();
    key = Key;
    const entity_type_id = await get_entity_type_id(sub);
    const postm = await post_media(sub, entity_type_id, key, name);
    return {
      result: key,
    };
  } catch (e) {
    return {
      result: e,
    };
  }
};
