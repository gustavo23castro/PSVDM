using System.Numerics;
using System.Runtime.CompilerServices;
using System.Runtime.Intrinsics;
using System.Runtime.Intrinsics.X86;

namespace FannkuchBenchmark;

public static class FannkuchCore
{
    private const int MAX_N = 16;

    private static readonly int[] _factorials;

    static FannkuchCore()
    {
        _factorials = new int[MAX_N + 1];
        _factorials[0] = 1;
        var factN = 1;
        for (var x = 0; x < MAX_N;)
        {
            factN *= ++x;
            _factorials[x] = factN;
        }
    }

    // Holds per-computation mutable state; replaces the original static fields.
    // Multiple threads share one RunState instance and synchronise via Interlocked.
    private sealed class RunState
    {
        public int N;
        public int BlockSize;
        public int BlockCount;  // decremented atomically by each thread to steal blocks
        public int Checksum;    // accumulated atomically across threads
        public int MaxFlips;    // updated atomically (CAS loop)
    }

    public static (int checksum, int maxFlips) ComputeSingle(int n)
    {
        var state = BuildState(n, nThreads: 1);
        PfannkuchThread(state);
        return (state.Checksum, state.MaxFlips);
    }

    public static (int checksum, int maxFlips) ComputeMulti(int n, int nThreads)
    {
        var state = BuildState(n, nThreads);
        var threads = new Thread[nThreads];
        for (var i = 1; i < nThreads; i++)
        {
            var s = state;
            (threads[i] = new Thread(() => PfannkuchThread(s))
            {
                IsBackground = true,
                Priority = ThreadPriority.Highest
            }).Start();
        }
        PfannkuchThread(state);
        for (var i = 1; i < threads.Length; i++)
            threads[i].Join();
        return (state.Checksum, state.MaxFlips);
    }

    private static RunState BuildState(int n, int nThreads)
    {
        // blockCount = 24 * nThreads keeps the same granularity as the original (4 threads → 96 blocks).
        // blockSize is truncated; the remainder of the permutation space falls in an extra partial block
        // that the while-loop handles naturally via blockId < 0 exit.
        var maxBlocksPerThread = 96 / 4;
        var blockCount = maxBlocksPerThread * nThreads;
        return new RunState
        {
            N = n,
            BlockCount = blockCount,
            BlockSize = _factorials[n] / blockCount,
        };
    }

    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    private static void PfannkuchThread(RunState state)
    {
        var masks_shift = new Vector128<byte>[16];
        var c0 = Vector128<byte>.Zero;
        var c1 = Vector128.Create((byte)1);
        var ramp = Vector128.Create((byte)0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15);
        var ramp1 = Sse2.ShiftRightLogical128BitLane(ramp, 1);
        var vX = Sse2.Subtract(c0, ramp);
        var old = ramp;
        for (var x = 0; x < MAX_N; x++)
        {
            var v2 = Sse41.BlendVariable(vX, ramp, vX);
            var v1 = Sse41.BlendVariable(ramp1, v2, Sse2.Subtract(vX, c1));
            old = Ssse3.Shuffle(old, v1);
            masks_shift[x] = old;
            vX = Sse2.Add(vX, c1);
        }

        var checksum = 0;
        var maxFlips = 0;
        int blockId;
        var n = state.N;
        var factorials = _factorials;
        var blockSize = state.BlockSize;

        while ((blockId = Interlocked.Decrement(ref state.BlockCount)) >= 0)
        {
            // Reconstruct the first permutation in this block from its rank.
            var next = ramp;
            var i = n;
            var j = blockSize * blockId;
            var countVector = c0;
            var blockLeft = blockSize;
            var mask = Sse2.Subtract(ramp, Vector128.Create((byte)i));
            while (i-- > 0)
            {
                var d = j / factorials[i];
                j -= d * factorials[i];
                var v2 = Vector128.Create((byte)d);
                countVector = Ssse3.AlignRight(countVector, v2, 15);
                var v1 = Sse2.Add(ramp, v2);
                var v0 = Sse2.Add(mask, v2);
                v0 = Sse41.BlendVariable(v0, v1, v0);
                v2 = Ssse3.Shuffle(next, v0);
                next = Sse41.BlendVariable(next, v2, mask);
                mask = Sse2.Add(mask, c1);
            }

            do
            {
                // Even step: checksum += flips
                var current = next;
                var v0 = Sse2.Subtract(countVector, ramp);
                var bits = BitOperations.TrailingZeroCount(Sse2.MoveMask(v0));
                v0 = Vector128.Create((byte)bits);
                var v1 = Sse2.AndNot(Sse2.CompareGreaterThan(v0.AsSByte(), ramp.AsSByte()).AsByte(), countVector);
                countVector = Sse2.Subtract(v1, Sse2.CompareEqual(v0, ramp));
                next = Ssse3.Shuffle(next, masks_shift[bits]);
                var first = Sse2.ConvertToInt32(current.AsInt32());
                {
                    var flips = 0;
                    var v3 = Ssse3.Shuffle(current, c0);
                    while ((first & 0xff) != 0)
                    {
                        v0 = Sse2.Subtract(v3, ramp);
                        v3 = Ssse3.Shuffle(current, v3);
                        v0 = Sse41.BlendVariable(v0, ramp, v0);
                        current = Ssse3.Shuffle(current, v0);
                        flips++;
                        first = Sse2.ConvertToInt32(v3.AsInt32());
                    }
                    checksum += flips;
                    if (flips > maxFlips) maxFlips = flips;
                }

                --blockLeft;
                if (blockLeft == 0) break;

                // Odd step: checksum -= flips
                current = next;
                v0 = Sse2.Subtract(countVector, ramp);
                bits = (byte)BitOperations.TrailingZeroCount(Sse2.MoveMask(v0));
                v0 = Vector128.Create((byte)bits);
                v1 = Sse2.AndNot(Sse2.CompareGreaterThan(v0.AsSByte(), ramp.AsSByte()).AsByte(), countVector);
                countVector = Sse2.Subtract(v1, Sse2.CompareEqual(v0, ramp));
                next = Ssse3.Shuffle(next, masks_shift[bits]);
                first = Sse2.ConvertToInt32(current.AsInt32());
                {
                    var flips = 0;
                    var v3 = Ssse3.Shuffle(current, c0);
                    while ((first & 0xff) != 0)
                    {
                        v0 = Sse2.Subtract(v3, ramp);
                        v3 = Ssse3.Shuffle(current, v3);
                        v0 = Sse41.BlendVariable(v0, ramp, v0);
                        current = Ssse3.Shuffle(current, v0);
                        flips++;
                        first = Sse2.ConvertToInt32(v3.AsInt32());
                    }
                    checksum -= flips;
                    if (flips > maxFlips) maxFlips = flips;
                }

                --blockLeft;
            } while (blockLeft != 0);
        }

        Interlocked.Add(ref state.Checksum, checksum);

        // CAS loop — update shared MaxFlips without a lock; safe because this runs once per thread.
        int current2;
        do
        {
            current2 = state.MaxFlips;
            if (maxFlips <= current2) break;
        } while (Interlocked.CompareExchange(ref state.MaxFlips, maxFlips, current2) != current2);
    }
}
