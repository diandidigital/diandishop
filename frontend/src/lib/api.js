import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'https://api.diandishop.com',  // Replace with your API URL
  timeout: 1000,
  headers: {'X-Custom-Header': 'foobar'},  // Replace with your custom headers if any
});

export default apiClient;