import { Client, Account, Databases, Storage } from 'appwrite';

const client = new Client();

const endpoint = process.env.NEXT_PUBLIC_APPWRITE_ENDPOINT;
const project = process.env.NEXT_PUBLIC_APPWRITE_PROJECT_ID;

if (!endpoint) {
    console.error('NEXT_PUBLIC_APPWRITE_ENDPOINT is not defined in .env.local');
}

if (!project) {
    console.error('NEXT_PUBLIC_APPWRITE_PROJECT_ID is not defined in .env.local');
}

client
    .setEndpoint(endpoint || 'http://localhost/v1') // Provide a valid-looking dummy to prevent crash if undefined
    .setProject(project || '');

export const account = new Account(client);
export const databases = new Databases(client);
export const storage = new Storage(client);
export { client };
