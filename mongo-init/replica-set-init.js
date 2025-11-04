const REPL_SET = "wonders-rs";
const HOST = "mongo:27777";
const SEARCH_USER = "mongotUser";
const SEARCH_PWD = "mongotPassword";
const SLEEP_MS = 3000;
const MAX_ATTEMPTS = 20;

function ensureReplicaSet() {
  try {
    const status = rs.status();
    if (status.set === REPL_SET) {
      try {
        const config = rs.conf();
        const member = config.members && config.members[0];
        if (member && member.host !== HOST) {
          if (status.myState !== 1) {
            print(
              `Replica set member host differs (${member.host}); current node not primary (state ${status.myState}). Skipping reconfig.`
            );
          } else {
            member.host = HOST;
            try {
              rs.reconfig(config, { force: true });
              print(`Replica set host updated to ${HOST}`);
            } catch (reconfigErr) {
              if (
                reconfigErr.codeName === "NotWritablePrimary" ||
                (reconfigErr.errmsg &&
                  reconfigErr.errmsg.includes("not primary"))
              ) {
                print(
                  "Skipping reconfig because node is not primary yet; will rely on existing configuration."
                );
              } else {
                throw reconfigErr;
              }
            }
          }
        } else {
          print(`Replica set already initialized: ${REPL_SET}`);
        }
      } catch (confErr) {
        const isNotPrimary =
          confErr.codeName === "NotWritablePrimary" ||
          (confErr.errmsg && confErr.errmsg.includes("not primary"));
        if (!isNotPrimary && confErr.codeName !== "NotYetInitialized") {
          throw confErr;
        }
      }
      return;
    }
  } catch (err) {
    if (err.codeName !== "NotYetInitialized") {
      throw err;
    }
  }

  const config = { _id: REPL_SET, members: [{ _id: 0, host: HOST }] };
  try {
    rs.initiate(config);
    print(`Replica set initiated: ${REPL_SET}`);
  } catch (err) {
    const alreadyInit =
      err.codeName === "AlreadyInitialized" ||
      err.code === 23 ||
      (err.errmsg && err.errmsg.includes("already initialized"));
    if (!alreadyInit) {
      throw err;
    }
    print(`Replica set already initialized (race): ${REPL_SET}`);
  }
}

function waitForPrimary() {
  let attempt = 0;
  while (attempt < MAX_ATTEMPTS) {
    try {
      const status = rs.status();
      const primary =
        status.members &&
        status.members.find((member) => member.stateStr === "PRIMARY");
      if (primary) {
        print("Replica set primary established.");
        return;
      }
    } catch (err) {
      if (err.codeName !== "NotYetInitialized") {
        throw err;
      }
    }
    print(
      `Waiting for replica set primary (attempt ${attempt + 1} of ${MAX_ATTEMPTS})...`
    );
    attempt += 1;
    sleep(SLEEP_MS);
  }
  throw new Error(
    `Replica set primary not ready after waiting ${(
      (SLEEP_MS * MAX_ATTEMPTS) /
      1000
    ).toFixed(0)} seconds.`
  );
}

function ensureSearchUser() {
  const adminDb = db.getSiblingDB("admin");
  const existing = adminDb.getUser(SEARCH_USER);
  if (existing) {
    print(`User ${SEARCH_USER} already exists, skipping creation.`);
    return;
  }

  function isWritablePrimary() {
    try {
      const hello = adminDb.runCommand({ hello: 1 });
      return Boolean(hello.isWritablePrimary ?? hello.ismaster ?? false);
    } catch (err) {
      if (isNotPrimaryError(err) || err.codeName === "NotYetInitialized") {
        return false;
      }
      throw err;
    }
  }

  function isNotPrimaryError(err) {
    if (!err) return false;
    const codes = [10107, 13435, 13436];
    return (
      (err.code && codes.includes(err.code)) ||
      err.codeName === "NotWritablePrimary" ||
      err.codeName === "NotPrimaryNoSecondaryOk" ||
      (err.errmsg && err.errmsg.includes("not primary"))
    );
  }

  let attempt = 0;
  while (attempt < MAX_ATTEMPTS) {
    try {
      if (!isWritablePrimary()) {
        throw Object.assign(new Error("Not primary yet"), {
          codeName: "NotWritablePrimary",
        });
      }
      adminDb.createUser({
        user: SEARCH_USER,
        pwd: SEARCH_PWD,
        roles: [{ role: "searchCoordinator", db: "admin" }],
      });
      print(`User ${SEARCH_USER} created.`);
      return;
    } catch (err) {
      if (isNotPrimaryError(err)) {
        print(
          `Waiting for primary before creating ${SEARCH_USER} (attempt ${
            attempt + 1
          } of ${MAX_ATTEMPTS})...`
        );
        attempt += 1;
        sleep(SLEEP_MS);
        continue;
      }
      throw err;
    }
  }
  throw new Error(
    `Failed to create ${SEARCH_USER}: primary not available after ${(
      (SLEEP_MS * MAX_ATTEMPTS) /
      1000
    ).toFixed(0)} seconds.`
  );
}

function ensureFactsNamespace() {
  const wwDb = db.getSiblingDB("ww");
  const collections = new Set(wwDb.getCollectionNames());
  if (collections.has("facts")) {
    print("Collection ww.facts already exists.");
    return;
  }
  wwDb.createCollection("facts");
  print("Collection ww.facts created.");
}

ensureReplicaSet();
waitForPrimary();
ensureSearchUser();
ensureFactsNamespace();
