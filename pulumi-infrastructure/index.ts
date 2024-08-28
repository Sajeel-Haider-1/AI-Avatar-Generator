import * as pulumi from "@pulumi/pulumi";
import * as gcp from "@pulumi/gcp";
import * as docker from "@pulumi/docker";
import * as dotenv from "dotenv";

dotenv.config();

const config = new pulumi.Config();

const location = process.env.LOCATION || "us-central1";
const serviceAccount = process.env.SERVICE_ACCOUNT || "";
const projectId = process.env.PROJECT_ID || "";
const serviceName = "my-cloud-run-service";
const artifactRepoName = process.env.ARTIFACT_REPO_NAME || "";
const imageName = process.env.IMAGE_NAME || "";

const firestoreIamBinding = new gcp.projects.IAMBinding("firestoreAdminRole", {
  project: projectId,
  role: "roles/datastore.owner",
  members: [pulumi.interpolate`serviceAccount:${serviceAccount}`],
});

const firestoreDatabase = new gcp.firestore.Database("aiAvatarFirestore", {
  locationId: "nam5",
  type: "FIRESTORE_NATIVE",
  name: "(default)",
});

const bucket = new gcp.storage.Bucket("ai_avatar_generator", {
  location: "US",
});

const bucketIamBinding = new gcp.storage.BucketIAMBinding(
  "bucketAdminBinding",
  {
    bucket: bucket.name,
    role: "roles/storage.objectAdmin",
    members: [pulumi.interpolate`serviceAccount:${serviceAccount}`],
  }
);

const artifactRegistry = new gcp.artifactregistry.Repository(artifactRepoName, {
  format: "DOCKER",
  location: location,
  repositoryId: artifactRepoName,
});

const fullImageName = pulumi.interpolate`${location}-docker.pkg.dev/${projectId}/${artifactRepoName}/${imageName}:v1`;

const image = new docker.Image(imageName, {
  imageName: fullImageName,
  build: {
    context: "../",
    platform: "linux/amd64",
  },
});

const cloudRunService = new gcp.cloudrun.Service(serviceName, {
  location: location,
  template: {
    spec: {
      containers: [
        {
          image: image.imageName,
          resources: {
            limits: {
              memory: "512Mi",
              cpu: "1",
            },
          },
        },
      ],
    },
  },
  traffics: [
    {
      percent: 100,
      latestRevision: true,
    },
  ],
});

const iamMember = new gcp.cloudrun.IamMember(`${serviceName}-public-access`, {
  service: cloudRunService.name,
  location: cloudRunService.location,
  role: "roles/run.invoker",
  member: "allUsers",
});
