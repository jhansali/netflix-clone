import useSWR from "swr";
import fetcher from '@/lib/fetcher';

const useMovieList = () => {
    const { data, error, isLoading } = useSWR('/api/movies', fetcher, {
        revalidateOnFocus: false,
        revalidateIfStale: false,
        revalidateOnReconnect: false,
    });

    return {
        data,
        isLoading,
        isError: error
    }
}

export default useMovieList;
