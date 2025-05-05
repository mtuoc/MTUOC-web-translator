These are the files for the MTUOC connector for Okapi Framework.

Building Okapi with the connector:
1. Clone the Okapi repository.
2. Copy the okapi directory to the root of the Okapi repository.
3. Add the data for the connector to the following files in the Okapi repository:
    applications/rainbow/pom.xml
    applications/tikal/pom.xml
    deployment/website/build.xml
    okapi-ui/swt/libraries/lib-translation-ui/src/main/java/net/sf/okapi/lib/ui/translation/DefaultConnectors.java
    okapi/connectors/pom.xml
    okapi/deployment/okapi-framework-sdk/pom.xml
4. Copy the applications directory to the root of the Okapi repository.
4. Run deployment/maven/build.sh ba in the Okapi repository.