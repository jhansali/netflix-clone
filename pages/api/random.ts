import { NextApiRequest, NextApiResponse } from "next";
import prismadb from "@/lib/prismadb";
import serverAuth from "@/lib/serverAuth";

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  try {
    await serverAuth(req, res);

    const moviesCount = await prismadb.movie.count();
    const randomIndex = Math.floor(Math.random() * moviesCount);

    const randomMovies = await prismadb.movie.findMany({
      take: 1,
      skip: randomIndex
    });

    if (randomMovies.length === 0) {
      return res.status(404).json({ error: 'No movies found' });
    }

    return res.status(200).json(randomMovies[0]);
  } catch (error) {
    // Instead of using console.error, we'll create an error response
    const errorMessage = error instanceof Error ? error.message : 'An unexpected error occurred';
    
    // Log the error to the server console
    console.log('API Error:', errorMessage);
    
    // Send the error response
    return res.status(500).json({ error: errorMessage });
  }
}
