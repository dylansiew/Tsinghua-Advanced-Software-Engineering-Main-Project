import axios from 'axios';

const baseURL = import.meta.env.VITE_API_URL;

export const sendMessage = async (user_id: string, message: string): Promise<any> => {
  const formData = new FormData();
  formData.append("user_id", user_id);
  formData.append("message", message);
  const response = await axios.post(`${baseURL}/conversation/${user_id}`, formData);
  return response.data;
};
