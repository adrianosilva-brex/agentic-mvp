export interface Provider {
  name: string;
  id: string;
  getEmbedUrl: () => Promise<string>;
}

export const ANON_PROVIDER: Provider = {
  name: 'Anon',
  id: 'anon',
  getEmbedUrl: async () => {
    const ANON_API_KEY = process.env.REACT_APP_ANON_API_KEY;
    const ANON_BASE_URL = process.env.REACT_APP_ANON_API_URL;

    const response = await fetch(`${ANON_BASE_URL}/api/v1/migration-modal`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${ANON_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: 'adriano.silva@brex.com',
        source_provider: 'navan'
      })
    });

    if (!response.ok) {
      throw new Error('Failed to get embed URL');
    }

    const data = await response.json();
    console.log(data)
    return data.url;
  }
};

// Add more providers here
export const PROVIDERS = [ANON_PROVIDER];